# PvZ-Auto-Coin-Collector
A fun little python script that detects silver, gold, and diamonds in Plants Vs. Zombies (first game) and collects them automatically.

It let's you select a region of the screen to detect coins then collect them if the match passes a 'confidence threshold'.

You can resume and pause the scrpt in real time, and the keybinds are changeable via keybinds.json file.

There is also some nice acurate statistics of what was collected, time, and total value.

Required modules for the python file is inside the `py/collectCoins folder`. You can use `pip install -r requirements.txt` to install what's required automatically. Alternatively, there is an exectuable version of the script inside `exe/collectCoins folder`.
