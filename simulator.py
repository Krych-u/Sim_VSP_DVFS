import network
import generate_user
import block_allocation
import priority_queue
import random
import update_data
import statistic


class Simulator:

    LAMBD = 0.6     # Lambda for users generator, higher lambda -> more users in network (0.05 can make big difference)
    RB_AL_TIME = 10   # Time between RB allocation
    RB_MAX_NB = 6    # Maximum RB number for each user
    RB_NUMBER = 50   # Number of all RBs
    UPDATE_TIME = 1  # Time between users received data update

    def __init__(self, logger, step_mode_):
        self.step_mode = step_mode_
        self.clock = 0  # Simulation time

        # Dictionary contains all random generators using in simulation
        self.random_container = self.generate_rand_dict()

        # Statistic object
        self.stats = statistic.Stat()

        self.log = logger
        self.sim_network = network.Network(self.log, Simulator.RB_AL_TIME, self.random_container, self.stats)

    def run(self, time):

        event_queue = priority_queue.PriorityQueue()

        # Creating events to start simulation
        first_user = generate_user.GenerateUser(self.log, event_queue,
                                                int(self.random_container["time"].expovariate(Simulator.LAMBD)),
                                                self.sim_network,
                                                Simulator.RB_MAX_NB, Simulator.RB_NUMBER, Simulator.RB_AL_TIME, self.random_container,
                                                Simulator.LAMBD)

        initial_rb_allocation = block_allocation.BlockAllocation(self.log, event_queue,
                                                                 Simulator.RB_AL_TIME, self.sim_network, Simulator.RB_MAX_NB,
                                                                 Simulator.RB_NUMBER, Simulator.RB_AL_TIME, Simulator.UPDATE_TIME,
                                                                 self.random_container, self.stats)

        first_data_update = update_data.UpdateData(self.log, event_queue,
                                                   Simulator.RB_AL_TIME + Simulator.UPDATE_TIME, self.sim_network,
                                                   Simulator.RB_MAX_NB, Simulator.RB_NUMBER, Simulator.RB_AL_TIME, Simulator.UPDATE_TIME,
                                                   self.random_container)

        # Initialization the simulation model using previously defined event objects
        event_queue.push(first_user, first_user.time)
        event_queue.push(initial_rb_allocation, Simulator.RB_AL_TIME)
        event_queue.push(first_data_update, first_data_update.time)

        # Main loop, actions in every iteration is implemented in execute virtual method
        while int(self.clock) <= int(time):
            event_ = event_queue.pop()
            self.clock = event_.return_time()
            event_.execute()

            self.log.info("Simulation time: " + str(self.clock) + " ms")

            if self.step_mode:
                input("Press any key to continue ... \n")

        self.stats.calc_stats()
        self.stats.display_stats()

    @staticmethod
    # Seeds dictionary
    def generate_rand_dict(
            time_seed=99,
            snr_seed=99,
            rb_nb_seed=99,
            data_seed=99
    ):
        # Time between user's appearance
        rand_time = random.Random()

        # Number of channel in snr directory
        rand_snr = random.Random()

        # Amount of RBs witch user expects
        rand_rb_nb = random.Random()

        # Random data amount for each UE
        rand_data = random.Random()

        # Setting seeds
        rand_time.seed(time_seed)
        rand_snr.seed(snr_seed)
        rand_rb_nb.seed(rb_nb_seed)
        rand_data.seed(data_seed)

        rand_dict = {
            "time": rand_time,
            "snr": rand_snr,
            "rb_number": rand_rb_nb,
            "data": rand_data
        }

        return rand_dict

