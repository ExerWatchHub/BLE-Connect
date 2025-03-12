import marimo

__generated_with = "0.11.17"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import holoviews as hv
    from bleak.backends.characteristic import BleakGATTCharacteristic
    from bleak import BleakClient, BleakScanner, BLEDevice, AdvertisementData
    import dearpygui.dearpygui as dpg
    import dearpygui.demo as demo
    import dearpygui_ext.themes as dpg_themes
    import logging
    import argparse
    from threading import Thread
    import asyncio
    import typing
    import platform
    import os
    import csv
    import time
    import datetime
    from icecream import ic
    return (
        AdvertisementData,
        BLEDevice,
        BleakClient,
        BleakGATTCharacteristic,
        BleakScanner,
        Thread,
        argparse,
        asyncio,
        csv,
        datetime,
        demo,
        dpg,
        dpg_themes,
        hv,
        ic,
        logging,
        mo,
        os,
        platform,
        time,
        typing,
    )


@app.cell
def _():
    import pandas as pd
    import math
    import numpy as np
    from tslearn.clustering import TimeSeriesKMeans
    from scipy.signal import argrelmin
    from tslearn.preprocessing import TimeSeriesResampler
    import tslearn.metrics
    from scipy.signal import find_peaks,argrelmin
    from scipy.signal import savgol_filter
    from scipy.signal import correlate, convolve

    return (
        TimeSeriesKMeans,
        TimeSeriesResampler,
        argrelmin,
        convolve,
        correlate,
        find_peaks,
        math,
        np,
        pd,
        savgol_filter,
        tslearn,
    )


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
