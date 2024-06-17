import numpy as np
import block_allocation


class User:
    RB_BANDWIDTH = 180  # Bandwidth of single RB  [kHz]
    MEAN_RB = 4         # Mean rb number

    def __init__(self, data, user_id, rb_nb, rand_cont, start_time):

        self.received_data = 0        # How many data has user received
        self.start_time = start_time  # Time when user appeared in network
        self.rb_amount = rb_nb        # Total number of rbs in network
        self.random_container = rand_cont

        self.user_id = user_id
        # List of SNR values for each RB
        self.snr_list = self.generate_snr()
        self.th_list = np.zeros((200, rb_nb))

        for i in range(200):
            for j in range(rb_nb):
                self.th_list[i][j] = block_allocation.BlockAllocation.shannon_th(self.snr_list[i][j])

        self.allocated_snr_list = []  # SNR list of currently allocated RBs
        self.throughput = 0           # Throughput depends on number of allocated RBs and SNR

        self.data = data              # data number

        self.rb_number = self.rb_number_generator(User.MEAN_RB, self.random_container['rb_number'])  # Expected RB number
        self.allocated_rb = 0         # Number of currently allocated RBs to this user
        self.allocated_rb_list = []   # list of allocated rbs

        return

    @staticmethod
    def rb_number_generator(mean_value, rand_gen):

        val = int(rand_gen.gauss(mean_value, 1.2))
        if val <= 0:
            val = 1

        return val

    def generate_snr(self):
        snr_str = 'snr'
        channel_nr = self.random_container[snr_str].randint(0, 9999)
        snr_list = np.genfromtxt(f'snr/channel_{channel_nr}', delimiter=',')

        snr_list = snr_list.T.tolist()

        return snr_list

    def calculate_throughput(self, time):

        th = 0
        snr = self.return_snr_list(time)

        for rb in self.allocated_rb_list:
            th += User.RB_BANDWIDTH * np.log2(1 + pow(10, snr[rb]/10))

        self.throughput = th
        return int(th)

    def allocation_array(self):
        array = np.zeros(self.rb_amount)
        for i in self.allocated_rb_list:
            array[i] = 1

        return array

    def return_ue_delay(self, time):
        return time - self.start_time

    # Returning SNR list from present time slot
    def return_snr_list(self, time):

        slot = (time - self.start_time)

        if slot > 199:
            #print(f'Slot out of range: {slot}')
            snr = self.snr_list[abs(200-slot) % 200]
        else:
            snr = self.snr_list[slot]

        return snr.copy()

    def return_th_list(self, time):

        snr_list = self.return_snr_list(time)
        th_list = []

        for snr in snr_list:
            th_list.append(User.RB_BANDWIDTH * np.log2(1 + pow(10, snr/10)))

        return th_list

    def wait_time(self, time):
        return time - self.start_time
