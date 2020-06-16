# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 14:48:28 2020

@author: Simon
"""

import numpy as np
import matplotlib.pyplot as plt
import math
import os
import json
import plotting_functions as pf
import pandas as pd
# import wandb
from keras import metrics
from data_functions import normalisation,overlap_data,read_overlap_data,downsample_data,DownsampleDataset
from keras.models import Sequential,Model,load_model
from keras.layers import Dense, concatenate, LSTM, TimeDistributed,Input
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.optimizers import Adam, RMSprop
from keras.utils import plot_model
from keras.callbacks import EarlyStopping, Callback, TensorBoard
# from wandb.keras import WandbCallback

np.random.seed(7)
# Hyper-parameters
timestep=100
input_size = 3
hidden_size = 193
num_layers = 1
batch_size = 100
output_dim = 2
lstm_hidden_units = 128
LR = 0.001
epoch=100

model_name = "sensor_bucharest"

# wandb.init(entity="mmloc",project=model_name,sync_tensorboard=True,
#            config={"epochs": epoch,"batch_size": batch_size,"hidden_size":hidden_size,
#                    "learning_rate":LR,"sensor_input_size":input_size,
#                    "output_dim":output_dim,"lstm_hidden_units":lstm_hidden_units
#                    }
#            )

train_sensor=DownsampleDataset()
SensorTrain=train_sensor.sensortrain
locationtrain=train_sensor.labeltrain
SensorVal=train_sensor.sensorval
locationval=train_sensor.labelval
SensorTest=train_sensor.sensortest
locationtest=train_sensor.labeltest

tensorboard = TensorBoard(log_dir='logs/{}'.format(model_name))
sensorinput=Input(shape=(SensorTrain.shape[1], SensorTrain.shape[2]))
sensorlstm=LSTM(input_shape=(SensorTrain.shape[1], SensorTrain.shape[2]),units=lstm_hidden_units)(sensorinput)
sensoroutput=Dense(output_dim)(sensorlstm)
model=Model(inputs=[sensorinput],outputs=[sensoroutput])

model.compile(optimizer=RMSprop(LR),
                 loss='mse',metrics=["acc"])

model.fit(SensorTrain, locationtrain,
                       validation_data=(SensorVal,locationval),
                       epochs=epoch, batch_size=batch_size, verbose=1,callbacks=[tensorboard]
                       #shuffle=False,
                       )

model.save("buchamodel/"+str(model_name)+".h5")
#model.save(os.path.join(wandb.run.dir, "wanbd_"+str(model_name)+".h5"))
fig1=plt.figure()
locPrediction = model.predict(SensorTest, batch_size=batch_size)
aveLocPrediction = pf.get_ave_prediction(locPrediction, batch_size)
data=pf.normalized_data_to_utm(np.hstack((locationtest, aveLocPrediction)))
plt.plot(data[:,0],data[:,1],'b',data[:,2],data[:,3],'r')
plt.legend(['target','prediction'],loc='upper right')
plt.xlabel("x-latitude")
plt.ylabel("y-longitude")
plt.title(str(model_name)+" Prediction")
fig1.savefig("buchapredictionpng/"+str(model_name)+"_locprediction.png")
#wandb.log({"chart": wandb.Image("romaniapredictionpng/"+str(model_name)+"_locprediction.png")})

#draw cdf picture
fig=plt.figure()
bin_edge,cdf=pf.cdfdiff(target=locationtest,predict=locPrediction)
plt.plot(bin_edge[0:-1],cdf,linestyle='--',label=str(model_name),color='r')
plt.xlim(xmin = 0)
plt.ylim((0,1))
plt.xlabel("metres")
plt.ylabel("CDF")
plt.legend(str(model_name),loc='upper right')
plt.grid(True)
plt.title((str(model_name)+' CDF'))
fig.savefig("buchacdf/"+str(model_name)+"_CDF.pdf")