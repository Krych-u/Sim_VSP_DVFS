import user
import block_allocation


class ResourceBlock:
    def __init__(self):
        self.throughput = 0
        self.snr = 0
        self.rb_user = None
        return

    def set_rb(self, user_, i):
        self.rb_user = user_
        self.throughput = user_.throughput[i]

    def is_free(self):
        if self.rb_user is None:
            return True
        return False


class Network:

    def __init__(self, logger, rb_al_time_, rand_gen, stat):
        self.rb_number = 50
        self.users_list = []
        self.rb_list = []
        self.rb_throughputs = []
        self.random_generator = rand_gen
        self.stat = stat

        for x in range(self.rb_number):
            self.rb_list.append(ResourceBlock())
            self.rb_throughputs.append(0)
        self.error_flag = False

        self.log = logger
        self.rb_al_time = rb_al_time_

        # Processor parameters
        self.v_min = 1.036  # V
        self.f_min = 0.8e9  # Hz
        self.v_mid = 1.276  # V
        self.f_mid = 1.2e9  # Hz
        self.v_max = 1.484  # V
        self.f_max = 1.6e9  # Hz

        self.p_min = 7      # W per second
        self.p_mid = 10     # W per second
        self.p_max = 25     # W per second

        # time multipliers for various frequencies:
        self.t_min = 2      # 2
        self.t_mid = 1.5    # 1
        self.t_max = 1      # 0

        # Current working frequency
        self.f_current = 0


    def clear_rb_list(self):
        i = 0
        for ite in self.rb_list:
            ite.rb_user = None
            ite.throughput = 0
            self.rb_throughputs[i] = 0
            i += 1

        for ite in self.users_list:
            ite.allocated_rb_number = 0

    def display_users_list(self):
        self.log.info("Users list: ")
        for user_ite in self.users_list:
            self.log.info(f"User [ ID: {str(user_ite.user_id)}, Data: {str(user_ite.data)}, Data received: {str(user_ite.received_data)}, expected rb number: {str(user_ite.rb_number)} ]")

    def update_received_data(self, update_time, time):

        users_to_delete = set()
        for us in self.users_list:
            us.calculate_throughput(time)

            # It means that user received all data
            if us.data <= us.throughput * update_time + us.received_data:
                us.received_data = us.data
                users_to_delete.add(us)

            # And here user did not received all data
            else:
                us.received_data += us.throughput * update_time

        # self.display_users_list()

        # Deleting users
        for us in users_to_delete:
            while 1:
                try:
                    self.rb_list[self.rb_list.index(us)].rb_user = None
                    self.rb_list[self.rb_list.index(us)].throughput = 0
                    self.rb_list[self.rb_list.index(us)].snr = 0

                except ValueError:
                    break

            # self.display_users_list()
            # self.log.debug("User id to delete: " + str(us.user_id))

            # Update stats
            self.stat.ue_th_list.append(us.data / (time - us.start_time))
            self.stat.wait_time.append(time - us.start_time)

            self.log.info("Deleting user nr " + str(us.user_id))
            self.users_list.remove(us)
        return

    def clear_rb(self):

        for rb in self.rb_list:
            rb.rb_user = None
            rb.throughput = 0
            rb.snr = 0

        for u in self.users_list:
            u.allocated_snr_list.clear()
            u.allocated_rb_list.clear()
            u.allocated_rb = 0

    def push_user_to_list(self, data, user_id, start_time):
        new_user = user.User(data, user_id, self.rb_number, self.random_generator, start_time)
        self.users_list.append(new_user)
        self.log.info("New user has been generated! [Id: " + str(user_id) + ", Data: " + str(data) + " bit]")
        self.log.info("Users in queue: " + str(len(self.users_list)))

        return

    def display_snr_list(self, time):
        self.log.debug("Users SNR list: ")
        for us in self.users_list:
            self.log.debug("User ID: " + str(us.user_id) + " ->  " + " ".join(map(str, us.return_snr_list(time))))

    def display_th_list(self, time):
        self.log.debug("Users Throughput list: ")
        for us in self.users_list:
            self.log.debug("User ID: " + str(us.user_id) + " RB request:" + str(us.rb_number) + " ->  " + " ".join(map(str, us.return_th_list(time))))

    def display_rbs(self):
        self.log.info("RB list after allocation: ")
        i = 0
        for rb in self.rb_list:
            i += 1
            if rb.rb_user is None:
                self.log.info(
                    " Block nr " + str(i) + " : User: [ ID: None , snr: None , throughput: 0]")
                continue

            self.log.info(f" Block nr {str(i)}: User: [ ID: {str(rb.rb_user.user_id)} , snr: {str(rb.snr)} , throughput: {str(rb.throughput)}]")

    # Return system throughput
    def return_sys_th(self):

        sum = 0
        for rb in self.rb_list:
            sum += rb.throughput

        return sum

    # Updating ue.rb_number resource blocks
    def update_rb(self, ue, rb, time):
        
        delay = time - ue.start_time

        for i in range(ue.rb_number):
            if rb >= self.rb_number or self.rb_list[rb].rb_user is not None:
                return ue.calculate_throughput(time), delay

            ue_snr = ue.return_snr_list(time)
            self.rb_list[rb].rb_user = ue
            self.rb_list[rb].snr = ue_snr[rb]
            self.rb_list[rb].throughput = block_allocation.BlockAllocation.shannon_th(ue_snr[rb])
            self.rb_throughputs[rb] = self.rb_list[rb].throughput
            ue.allocated_snr_list.append(ue_snr[rb])
            ue.allocated_rb_list.append(rb)
            ue.allocated_rb += 1
            rb += 1

        ue_th = ue.calculate_throughput(time)

        return ue_th, delay

    def update_rb2(self, user_id, rb, time):

        delay = 100000
        ue = None
        for u in self.users_list:
            if u.user_id == user_id:
                ue = u
                delay = ue.return_ue_delay(time)
                break

        for i in range(ue.rb_number):
            if rb >= self.rb_number:
                return rb, ue.calculate_throughput(time), delay

            ue_snr = ue.return_snr_list(time)
            self.rb_list[rb].rb_user = ue
            self.rb_list[rb].snr = ue_snr[rb]
            self.rb_list[rb].throughput = block_allocation.BlockAllocation.shannon_th(ue_snr[rb])
            self.rb_throughputs[rb] = self.rb_list[rb].throughput
            ue.allocated_snr_list.append(ue_snr[rb])
            ue.allocated_rb_list.append(rb)
            ue.allocated_rb += 1
            rb += 1

        ue_th = ue.calculate_throughput(time)

        return rb, ue_th, delay

    # Returning mean delay in network
    def return_delay(self, time):
        delay = 0
        i = 0

        for ue in self.users_list:
            i += 1
            delay += time - ue.start_time
        if i > 0:
            delay = delay / i

        return delay

    def return_rb_delay(self, time):
        delay = 0
        i = 0

        for rb in self.rb_list:

            # In case of an empty rb
            if rb.rb_user is None:
                continue
            i += 1
            delay += time - rb.rb_user.start_time

        # In case of an empty network
        if i > 0:
            delay = delay / i

        return delay

    def mean_us_th(self, time):

        th = 0
        i = 0

        for ue in self.users_list:
            if ue.allocated_rb > 0:
                th += ue.calculate_throughput(time)
                i += 1

        if i > 0:
            return th / i
        else:
            return 0

    def free_rb(self):

        for rb in self.rb_list:
            if rb.rb_user is None:
                return True

        return False

    def return_sys_th_list(self):

        th_list = []
        for rb in self.rb_list:
            if rb.throughput > 0:
                th_list.append(0)
            else:
                th_list.append(1)

        return th_list

    def return_time_multiplier(self):
        if self.f_current == 0:
            return self.t_max
        if self.f_current == 1:
            return self.t_mid
        if self.f_current == 2:
            return self.t_min

    def return_power_usage(self):
        if self.f_current == 0:
            return self.p_max
        if self.f_current == 1:
            return self.p_mid
        if self.f_current == 2:
            return self.p_min
