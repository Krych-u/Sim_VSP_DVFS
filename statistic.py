import matplotlib.pyplot as plt
import numpy as np


class Stat:
    def __init__(self):
        # Stats collecting during simulation
        self.ue_th_list = []       # List of th every UE throughput
        self.sys_th_list = []      # List of th of system
        self.wait_time = []        # How long users were waiting to receive all data
        self.running_time = []     # Allocation time; how long is algorithm calculating

        # Stats to calculate after simulation
        self.av_th = 0
        self.sys_av_th = 0
        self.sys_av_th_list = []
        self.av_wait_time = 0
        self.rb_all_time_list = []
        self.run_time = 0

        # Power usage
        self.energy_consumption = []
        self.energy_consumption_total = 0
        self.load = []

    def calc_stats(self, rb_all_time=10):
        self.av_th = sum(self.ue_th_list[0:len(self.ue_th_list)]) / len(self.ue_th_list)
        self.av_wait_time = sum(self.wait_time[0:len(self.wait_time)]) / len(self.wait_time)

        self.rb_all_time_list = np.linspace(rb_all_time, rb_all_time*len(self.sys_th_list), len(self.sys_th_list))
        self.run_time = sum(self.running_time[0:len(self.running_time)]) / len(self.running_time)
        self.energy_consumption_total = sum(self.energy_consumption[0:len(self.energy_consumption)])

    def display_stats(self):

        print(f'Average UE throughput: {self.av_th} kbps')
        print(f'Average wait time: {self.av_wait_time} s')
        print(f'Average system throughput: {self.return_av_th()} kbps')
        print(f'Average run time: {self.run_time} s')
        print(f'Total allocation energy consumption: {self.energy_consumption_total} W')

        plt.plot(self.rb_all_time_list, self.sys_av_th_list)
        plt.xlabel('Czas symulacji [ms]')
        plt.ylabel('Przepływność [kbps]')
        plt.title('Przepływność systemu')
        plt.axis('tight')
        plt.grid()
        plt.show()

        plt.hist(self.ue_th_list, bins=int(len(self.ue_th_list)/10))
        plt.ylabel('Ilość użytkowników')
        plt.xlabel('Przepływność użytkownika [kbps]')
        plt.grid()
        plt.show()

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

        ax1.plot(self.rb_all_time_list, self.running_time)
        ax1.set_xlabel('Czas symulacji [ms]')
        ax1.set_ylabel('Czas wykonywania algorytmu[s]')
        ax1.set_title('Czas działania algorytmu')
        ax1.grid()

        ax2.plot(self.rb_all_time_list, self.energy_consumption)
        ax2.set_xlabel('Czas symulacji [ms]')
        ax2.set_ylabel('Energia [J]')
        ax2.set_title('Zużycie energii')
        ax2.grid()

        plt.tight_layout()
        plt.show()

        if len(self.load) > 0:
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))

            ax1.plot(self.rb_all_time_list, self.running_time)
            ax1.set_xlabel('Czas symulacji [ms]')
            ax1.set_ylabel('Czas wykonywania algorytmu[s]')
            ax1.set_title('Czas działania algorytmu')
            ax1.grid()

            ax2.plot(self.rb_all_time_list, self.energy_consumption)
            ax2.set_xlabel('Czas symulacji [ms]')
            ax2.set_ylabel('Energia [J]')
            ax2.set_title('Zużycie energii')
            ax2.grid()

            ax3.plot(self.rb_all_time_list, self.load)
            ax3.set_xlabel('Czas symulacji [ms]')
            ax3.set_ylabel('Parametr load')
            ax3.set_title('Parametr load')
            ax3.grid()

            plt.tight_layout()
            plt.show()

    def return_av_th(self):
        if len(self.sys_av_th_list) > 0:
            return self.sys_av_th_list[-1]
        else:
            return 0
