from . import pd
from . import np
from . import os
from . import datetime

from . import sparse
from . import spsolve
from . import timedelta

from . import MaxAbsScaler

class Preprocessing():
    def __init__(self, path="../static/csv-upload/", sep=",", fs=250, sample_size=6):
        self.path = path
        self.sep = sep
        self.fs = fs
        self.sample_size = sample_size
        self.filename = ""

    def read_csv_to_df(self, filename, path, sep=";"):
        self.filename = os.path.basename(filename)
        df = pd.read_csv(os.path.join(path, filename), sep=sep, skiprows = [0])
        print("\n\n[INFO] finish read file - %s\n\n" % filename)

        #df = df.drop(0) 
        df.columns = ['Time', 'ECG1', 'ECG2']

        df['ECG1'] = pd.to_numeric(df['ECG1'])
        df['ECG2'] = pd.to_numeric(df['ECG2'])

        # peak reduction
        df[df['ECG1'] > 2] = 2
        df[df['ECG1'] < -2] = -2
        df[df['ECG2'] > 2] = 2
        df[df['ECG2'] < -2] = -2
        print("\n\n[INFO] finish data cleansing - %s\n\n" % filename)

        df["Time"] = df['Time'].str.replace("[", "")
        df["Time"] = df['Time'].str.replace("]", "")
        df["Time"] = df['Time'].str.replace("'", "")

        df["Time"] = pd.to_datetime(df["Time"], errors='coerce')
        print("\n\n[INFO] finish time cleansing -  %s\n\n" % filename)

        df.set_index("Time", inplace=True)
        return df

    def baseline_als(self, y, lam=10000, p=0.05, n_iter=10):
        L = len(y)
        D = sparse.diags([1,-2,1],[0,-1,-2], shape=(L,L-2))
        w = np.ones(L)
        for i in range(n_iter):
            W = sparse.spdiags(w, 0, L, L)
            Z = W + lam * D.dot(D.transpose())
            z = spsolve(Z, w*y)
            w = p * (y > z) + (1-p) * (y < z)
        return z

    def perdelta(self, start, end, delta):
        curr = start
        while curr < end:
            yield curr
            curr += delta
            
    def remove_baseline_als(self, ECG):
        time_interval = [time_result for time_result in self.perdelta(ECG.index.min(), ECG.index.max(), timedelta(seconds=16))]
        ECG_ALS = []
        for time_intv in list(zip(time_interval, time_interval[1:])):
            X = ECG.between_time(time_intv[0].time(), time_intv[1].time())
            if len(X) > 0 and (X.index[-1] - X.index[0]).total_seconds() >= self.sample_size :
                ecg1 = X['ECG1'].values
                ecg2 = X['ECG2'].values

                if len(ecg1) > 0 and len(ecg2) > 0:
                    ALS1 = ecg1 - self.baseline_als(ecg1)
                    ALS2 = ecg2 - self.baseline_als(ecg2)

                    ECG_ALS.append(np.array([ALS1, ALS2]))
        return ECG_ALS

    def min_max_normalization(self, ECG_ALS):
        scaler = MaxAbsScaler()
        ECG_ALS_Norm = []

        for als in ECG_ALS :
            als1 = np.expand_dims(als[0], 1)
            als2 = np.expand_dims(als[1], 1)

            scaler.fit(als1)

            als_norm1 = scaler.transform(als1)
            als_norm2 = scaler.transform(als2)

            ECG_ALS_Norm.append([als_norm1, als_norm2])
        return ECG_ALS_Norm

        print("[INFO] upsampling signal to 250Hz ...")
        
    def upsampling_twice(self, data):
        # upsampling interpolation
        result = np.zeros(2*len(data)-1)
        result[0::2] = data
        result[1::2] = (data[1:] + data[:-1]) / 2
        return result
    
    def upsampling(self, ECG_ALS_Norm)
        new_fs = 250 # Hz 
        ECG_ALS_Norm_Up = []
        for data in ECG_ALS_Norm :
            data1 = np.array(data[0][:,0])
            data2 = np.array(data[1][:,0])
            data1 = upsampling_twice(data1).reshape(-1, 1)  
            data2 = upsampling_twice(data2).reshape(-1, 1)  
            ECG_ALS_Norm_Up.append([data1, data2])
        return ECG_ALS_Norm_Up
        
    def transform(self, filename):
        print("\n\n[INFO] Read CSV...\n\n")
        ECG = self.read_csv_to_df(filename, self.path, sep=self.sep)
        print("\n\n[INFO] Apply Baseline Wander Removal...\n\n")
        ECG_ALS = self.remove_baseline_als(ECG)
        print("\n\n[INFO] Apply Signal Normalization...\n\n")
        ECG_ALS_Norm = self.min_max_normalization(ECG_ALS)

        data = []
        pad_size = self.sample_size*self.fs # 6s x 250hz
        print("\n\n[INFO] Apply padding data with pad_size=%d...\n\n" % pad_size)
        for i in range(len(ECG_ALS_Norm)):
            signal_ch = []
            for ch in [0, 1] :
                signal = np.array(ECG_ALS_Norm[i])[ch, :, 0]
                n = len(signal) if len(signal) <= pad_size else pad_size
                pad = np.zeros(pad_size)
                pad[0:n] = signal[0:n] 
                signal_ch.extend(list(pad))    
            data.append(signal_ch)
        print("[INFO] Finish applying padding...")
        return pd.DataFrame(data)