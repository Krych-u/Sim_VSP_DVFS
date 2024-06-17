import event
import user
import numpy as np
from timeit import default_timer as timer


class BlockAllocation(event.Event):

    # Chosen algorithm
    ALGORITHM_TYPE = 2
    DVFS = 1

    def __init__(self, logger, event_queue_, time_, sim_network_, rb_max_nb_, rb_number_, rb_al_time_, update_time, rand_cont, stats):
        super().__init__(logger, event_queue_, time_, sim_network_, rb_max_nb_, rb_number_, rb_al_time_, rand_cont)
        self.update_time = update_time
        self.stats = stats

    def execute(self):

        # Updating received data
        self.sim_network.update_received_data(self.update_time, self.time)
        self.sim_network.clear_rb()

        time_multiplier = self.sim_network.return_time_multiplier()
        start = timer()

        # RB allocation
        if self.ALGORITHM_TYPE == 0:
            self.log.info("RB allocation using maximum throughput algorithm")
            self.max_th()

        elif self.ALGORITHM_TYPE == 1:
            self.log.info("RB allocation using round robin algorithm")
            self.round_robin()

        elif self.ALGORITHM_TYPE == 2:
            self.log.info("RB allocation using heuristic power aware VSP-DVFS algorithm")
            load = self.heuristic_vsp_dvfs()
            self.stats.load.append(load)

        stop = timer() - start
        self.stats.running_time.append(stop * time_multiplier)
        self.stats.energy_consumption.append(self.stats.running_time[-1] * self.sim_network.return_power_usage())
        self.log.debug("Time multiplier = " + str(time_multiplier))
        self.log.debug("Running time = " + str(self.stats.running_time[-1]) + ' RT without multiplication: ' + str(stop))

        # Update stats - system throughput
        self.stats.sys_th_list.append(self.sim_network.return_sys_th())
        self.stats.sys_av_th_list.append(sum(self.stats.sys_th_list) / len(self.stats.sys_th_list))

        # Display current network status
        self.sim_network.display_snr_list(self.time)
        self.sim_network.display_th_list(self.time)
        self.sim_network.display_rbs()

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------
        # Adding next rb_allocation event to event queue
        next_rb_allocation = BlockAllocation(self.log, self.event_queue,
                                             self.rb_al_time + self.time, self.sim_network,
                                             self.rb_max_nb, self.rb_number, self.rb_al_time, self.update_time,
                                             self.random_container, self.stats)
        self.event_queue.push(next_rb_allocation, next_rb_allocation.time)

        return

    def max_th(self):

        rb = 0
        while rb < self.sim_network.rb_number:

            max_thr = 0
            max_ue = None

            for ue in self.sim_network.users_list:

                if ue.rb_number == ue.allocated_rb:
                    continue

                ue_th_list = ue.return_th_list(self.time)

                if rb+ue.rb_number < self.sim_network.rb_number:
                    ue_th = sum(ue_th_list[rb:rb+ue.rb_number]) / ue.rb_number
                else:
                    ue_th = sum(ue_th_list[rb:self.sim_network.rb_number-1]) / self.sim_network.rb_number - rb

                if ue_th > max_thr:
                    max_thr = ue_th
                    max_ue = ue

            if max_ue is None:
                break

            self.sim_network.update_rb2(max_ue.user_id, rb, self.time)
            max_ue.throughput = max_ue.calculate_throughput(self.time)
            rb += max_ue.rb_number

    def round_robin(self):

        i = 0
        for user in self.sim_network.users_list:
            if i == len(self.sim_network.rb_list) - 1:
                break

            for rb in range(user.rb_number):
                if i == len(self.sim_network.rb_list) - 1:
                    break

                self.sim_network.rb_list[i].rb_user = user
                snr_l = user.return_snr_list(self.time)
                self.sim_network.rb_list[i].snr = snr_l[i]
                user.allocated_snr_list.append(snr_l[i])
                self.sim_network.rb_list[i].throughput = self.shannon_th(snr_l[i])
                user.allocated_rb_list.append(i)

                i += 1

            user.throughput = user.calculate_throughput(self.time)

        return

    def heuristic_vsp_dvfs(self):

      # 1. Sort users
        sorted_users = self.sort_users(self)

      # 2. Allocate resources

        # Clean throughput list
        self.sim_network.clear_rb_list()

        for ue_ite in sorted_users:
            ue = ue_ite[0]  # ue_ite is list of pairs user-wait time

            self.log.debug("User id: " + str(ue.user_id) + ' wait time: ' + str(ue.wait_time(self.time)))
            ue_th_list = ue.return_th_list(self.time)

            # Update list with 0 in already allocated RBs
            for i in range(len(ue_th_list)):
                if self.sim_network.rb_throughputs[i] != 0:
                    ue_th_list[i] = 0

            i = 0
            max_val = 0       # max calculated throughput for LB HB blocks
            LB = -1           # Lower-bound: low index of maxValue bound of blocks
            HB = -1           # Higher-bound: high index of maxValue bound of blocks
            while i < self.sim_network.rb_number:

                # If RB is not free - continue to next RB
                if ue_th_list[i] == 0:
                    i += 1
                    continue

                # Free RB, calculate throughput of next RBs that can be allocated
                rb_nr = i
                current_th = 0   # Throughput calculated for current RB string
                while rb_nr <= i+ue.rb_number and rb_nr < self.sim_network.rb_number:
                    current_th += ue_th_list[rb_nr]
                    if ue_th_list[rb_nr] == 0 or rb_nr == i+ue.rb_number-1 or rb_nr == self.sim_network.rb_number-1:
                        break
                    else:
                        rb_nr += 1

                if current_th > max_val:
                    max_val = current_th
                    LB = i
                    HB = rb_nr

                i += 1

            j = LB

            # Update network
            while j <= HB:

                self.sim_network.rb_list[j].rb_user = ue
                snr_l = ue.return_snr_list(self.time)
                self.sim_network.rb_list[j].snr = snr_l[j]
                ue.allocated_snr_list.append(snr_l[j])
                self.sim_network.rb_list[j].throughput = self.shannon_th(snr_l[j])
                ue.allocated_rb_list.append(j)
                self.sim_network.rb_throughputs[j] = ue_th_list[j]

                j += 1

            ue.throughput = ue.calculate_throughput(self.time)

      # 3. Calculate processor load and and adjust processor speed
        load = 1
        # If it is first allocation - use max frequency
        if len(self.stats.running_time) == 0 or BlockAllocation.DVFS == 0:
            self.sim_network.f_current = 0
            return load

        # load
        t_aloc = self.stats.running_time[-1]
        t_max_aloc = 0.01
        allocated_blocks = self.allocated_blocks(self)

        load = (allocated_blocks / self.sim_network.rb_number) * (t_aloc / t_max_aloc)

        # Adjust processor speed:
        if load >= 0.66:
            self.sim_network.f_current = 0
        elif 0.66 > load >= 0.33:
            self.sim_network.f_current = 1
        else:
            self.sim_network.f_current = 2

        self.log.debug("Frequency number = " + str(self.sim_network.f_current))
        self.log.debug("Load = " + str(load) + " Load params [t_aloc, t_max_aloc, allocated_blocks]: " + str(t_aloc) + ' ' + str(t_max_aloc) + ' ' + str(allocated_blocks))

        return load

    def proportional_fair(self):

        return

    @staticmethod
    def sort_users(self):

        # Create list of users with User object and its priority
        users_list = []
        for ue in self.sim_network.users_list:
            users_list.append((ue, ue.wait_time(self.time)))

        sorted_users = sorted(users_list, key=lambda x: x[1], reverse=True)
        return sorted_users

    @staticmethod
    def shannon_th(snr):
        return int(user.User.RB_BANDWIDTH * np.log2(1 + BlockAllocation.dec2lin(snr)))

    @staticmethod
    def dec2lin(val):
        return pow(10, val/10)

    @staticmethod
    def allocated_blocks(self):
        allocated_blocks = self.sim_network.rb_number
        for rb in self.sim_network.rb_throughputs:
            if rb == 0:
                allocated_blocks -= 1

        return allocated_blocks



