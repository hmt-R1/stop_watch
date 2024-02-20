import RPi.GPIO as GPIO
import time
import threading
import sys

SDI = 24
RCLK = 23
SRCLK = 18

# 10:SPIMOSI
# GPIO22 -> GPIO12
# GPIO27 -> GPIO4
# GPIO17 -> GPIO13
placePin = (10, 12, 4, 13)

# 4桁7segLEDに表示させる数字の値
number = (0xc0, 0xf9, 0xa4, 0xb0, 0x99, 0x92, 0x82, 0xf8,
					0x80, 0x90)

# LEDに繋がるGPIOピン番号
LedPin = 17

# タイマーカウント用スレッド変数
timer1 = 0

# LED発光用スレッド変数
timer2 = 0

# ブザー用スレッド変数
timer3 = 0

# カウンター
counter = 0

# 一時停止時にカウンター値保存
tcounter = 0

# ブザーに繋がっているGPIOピン番号
BeepPin = 27

# ボタン:GPIO5 -> スタート・ストップボタン
BUTTON = 5

# ボタンR:GPIO6 -> リセットボタン
BUTTON_R = 6

# ボタンの状態
g_button = False

# ボタンRの状態
g_button_r = False

# システム状態を表す変数
# 0 -> 初期状態, 1 -> 処理中状態, 2 -> チャタリング状態
status = 0

# ボタンが押された回数の状態を表す変数
# False: 開始->停止, True: 停止->開始
btn_status = False

# 4桁7segLEDデスプレイ表示を消す
def clearDisplay():
	global SDI
	global SRCLK
	global RCLK

	for i in range(8):
		GPIO.output(SDI, 1)
		GPIO.output(SRCLK, GPIO.HIGH)
		GPIO.output(SRCLK, GPIO.LOW)
	GPIO.output(RCLK, GPIO.HIGH)
	GPIO.output(RCLK, GPIO.LOW)

# 4桁7segLEDに指定数字を表示
def hc595_shift(data):
	global SDI
	global SRCLK
	global RCLK

	for i in range(8):
		GPIO.output(SDI, 0x80 & (data << i))
		GPIO.output(SRCLK, GPIO.HIGH)
		GPIO.output(SRCLK, GPIO.LOW)
	GPIO.output(RCLK, GPIO.HIGH)
	GPIO.output(RCLK, GPIO.LOW)

# 4桁7segLEDの表示桁を選択
def pickDigit(digit):
	global placePin

	for i in placePin:
		GPIO.output(i, GPIO.LOW)
	GPIO.output(placePin[digit], GPIO.HIGH)

# 初期化
def setup():
	# GPIOピン番号をBCM番号に設定
	GPIO.setmode(GPIO.BCM)

	# LEDに繋がるGPIOピンを出力設定,初期出力値をHIGH
	GPIO.setup(LedPin, GPIO.OUT, initial = GPIO.LOW)

	# ブザーピンを出力設定,初期出力値をHIGHに設定
	GPIO.setup(BeepPin, GPIO.OUT, initial = GPIO.HIGH)

	# 4桁7segLEDピンの設定
	GPIO.setup(SDI, GPIO.OUT)
	GPIO.setup(RCLK, GPIO.OUT)
	GPIO.setup(SRCLK, GPIO.OUT)
	for i in placePin:
		GPIO.setup(i, GPIO.OUT)

	# スタート・ストップボタン
	# ボタンが繋がるGPIOピン動作:入力,プルアップ
	GPIO.setup(BUTTON, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	# 立ち下がり検出
	GPIO.add_event_detect(BUTTON, GPIO.FALLING, bouncetime = 100)
	# コールバック関数を登録
	GPIO.add_event_callback(BUTTON, sw)

	# リセットボタン
	# ボタンが繋がるGPIOピン動作:入力,プルアップ
	GPIO.setup(BUTTON_R, GPIO.IN, pull_up_down = GPIO.PUD_UP)
	# 立ち下がり検出
	GPIO.add_event_detect(BUTTON_R, GPIO.FALLING, bouncetime = 100)
	# コールバック関数を登録
	GPIO.add_event_callback(BUTTON_R, rsw)

	# タイマーカウント用スレッド関数を処理
	# 0.1秒毎にtimer関数を呼び出し
	#timer1 = threading.Timer(0.1, timer)
	#timer1.start()

	# LED発光用スレッド関数を処理
	#timer2 = threading.Timer(0.5, timer_n2)
	#timer2.start()

	# ブザー用スレッド関数を処理
	#timer3 = threading.Timer(0.5, timer_n3)
	#timer3.start()

# スタート・ストップスイッチ押下時,
# 呼び出されるコールバック関数
def sw(gpio_no):
	global g_button
	global btn_status
	global counter
	global tcounter

	# ボタン押下時Trueにする
	g_button = True

	# ボタン押下状態を反転
	btn_status = not btn_status

	# 保存カウンター値にカウンター値を代入
	tcounter = counter

	# ボタン押下され,開始状態の時->btn_status == True
	# ボタン押下され,停止状態の時->btn_status == False
	# ボタン押下状態: 一時停止状態
	# この時のカウンター値を保存
	if btn_status == False:
		tcounter = counter
	# ボタン押下状態: 開始状態
	# 停止時のカウンター値を代入
	elif btn_status == True:
		counter = tcounter

# MEMO btn_status
# 初期状態: btn_status -> False
# 初期状態->ボタン押下1: btn_status -> True :開始状態
#												 counter = tcounter
#                        値は0
# ボタン押下1->ボタン押下2: btn_status -> False :停止状態
#                        tcounter = counter
#												 tcounter値を表示
#                        例.値は3
# ボタン押下2->ボタン押下3: btn_status -> True :開始状態
#												 counter = tcounter
#												 例.値は3


# リセットボタン押下時,実行
def rsw(gpio_no):
	global g_button_r
	global g_button
	global btn_status
	global counter
	global tcounter

	# リセットボタン押下状態をTrue
	g_button_r = True

	# スタート・ストップボタン押下状態を初期化
	g_button = False

	# ボタン押下状態を一時停止
	btn_status = False

	# カウンター値を0
	counter = 0
	tcounter = 0

# モニター表示カウンター用のスレッド関数
def timer():
	global timer1
	global counter
	global LedPin
	global tcounter
	global btn_status
	global g_button_r
	global g_button
	global status

	# 0.1秒毎にtimer関数を呼び出し
	timer1 = threading.Timer(0.1, timer)
	# スレッドを開始
	timer1.start()

# ボタン押下状態:開始状態の時
	if btn_status == True:
		# モニターにcounter値を表示
		print('\r{}{}{}.{}'.format(((counter % 10000) // 1000), ((counter % 1000) // 100), ((counter % 100) // 10), (counter % 10)), end = '')

		# カウンター値を1進める
		counter += 1

# ボタン押下状態:一時停止状態の時
	elif btn_status == False:
		# モニターにtcounter値を表示
		print('\r{}{}{}.{}'.format(((tcounter % 10000) // 1000), ((tcounter % 1000) // 100), ((tcounter % 100) // 10), (tcounter % 10)), end = '')

# LED発光・消灯用変数
ln = False

# LED発光用スレッド関数
def timer_n2():
	global timer2
	global ln
	global btn_status
	global g_button
	global g_button_r

	timer2 = threading.Timer(0.5, timer_n2)
	timer2.start()

# ボタン押下状態:開始状態の時
	if btn_status == True:
		# 発光・消灯を切り替え
		ln = not ln

		# LEDを発光 or 消灯させる
		led1(int(ln))

# ボタン押下状態:一時停止状態の時
	elif btn_status == False:
		# LEDを消灯させる
		led1(0)

# リセットボタン押下時
	if g_button_r == True:
		# LEDを消灯
		led1(0)

# ブザーON/OFF用変数
bn = False

# ブザー用スレッド関数
def timer_n3():
	global timer3
	global bn
	global g_button
	global g_button_r
	global btn_status

	# 0.5秒毎にtimer_n3関数を呼び出し
	timer3 = threading.Timer(0.5, timer_n3)
	# スレッドを開始
	timer3.start()

# ボタン押下状態:開始中状態の時
	if btn_status == True:
		# ブザー状態ON/OFF切り替え
		bn = not bn

		# ブザーを鳴らす
		buzzer1(int(bn))

# ボタン押下状態:一時停止中状態の時
	if btn_status == False:
		# ブザーを止める
		buzzer1(GPIO.HIGH)

# リセットボタン押下の時
	if g_button_r == True:
		# ブザーを止める
		buzzer1(GPIO.HIGH)

# LEDを発光
def led1(n):
	# LEDを発光 or 消灯させる
	GPIO.output(LedPin, n)

# ブザーを鳴らす
def buzzer1(n):
	# ブザーをオンにし鳴らす
	GPIO.output(BeepPin, n)
	time.sleep(0.000001)
	# ブザーをオフにする
	GPIO.output(BeepPin, GPIO.HIGH)

# 4桁7segLEDを順番に一桁ずつ高速に発光させる
def Seven_segLED(cntr):
	clearDisplay()
	pickDigit(0)
	hc595_shift(number[cntr % 10])

	clearDisplay()
	pickDigit(1)
	# & 0x7f -> ドットを表示させる演算
	hc595_shift((number[cntr % 100 // 10] & 0x7f))

	clearDisplay()
	pickDigit(2)
	hc595_shift(number[cntr % 1000 // 100])

	clearDisplay()
	pickDigit(3)
	hc595_shift(number[cntr % 10000 // 1000])

# MEMO
# 0 10(10*(10**0))    1(10**0)
# 1 100(10*(10**1))   10(10**1) :ドットを付ける
# 2 1000(10*(10**2))  100(10**2)
# 3 10000(10*(10**3)) 1000(10**3)
# -> (counter % (10*(10**i))) // (10**i)

# 主処理
def main():
	try:
		global counter
		global tcounter
		global g_button		# ボタン押下・非押下
		global g_button_r	# ボタン押下・非押下
		global LedPin
		global btn_status

		n = False
		g_button = False
		g_button_r = False
		# g_button, g_button_r
		# ボタン押下   -> True
		# ボタン非押下 -> False

		resume = 0

		# status: プログラムの処理状態
		# status -> 0:初期状態
		#           1:処理中状態
		#           2:チャタリング状態
		status = 0
	
		# ボタン押下状態 -> False:開始->停止, True:停止->開始
		btn_status = False

		# 初期化実行
		setup()

		print('******************* ストップウォッチ *********************')
		print('タイマー          : 0.1秒毎進む')
		print('0.5秒毎           : LEDが発光,ビープ音が鳴る')
		print('スイッチ押下毎    : スタート or ストップ')
		print('リセットボタン押下: タイマーリセット,LED消灯,ビープ音停止')
		print('プログラム終了    : キーボードCtrl+cを押下')
		print('**********************************************************')

		while True:
# プログラムの処理状態:初期状態の時
			if status == 0:
				while True:
					# スタート・ストップボタン押下時
					if g_button == True:
						# チャタリング状態に移行
						status = 2

						# 4桁7segLEDに0を表示
						Seven_segLED(1)

						# モニター表示を改行する
						print()

						# モニター表示カウンタースレッド関数を処理,開始
						# 0.1秒毎にtimer関数を呼び出し
						timer1 = threading.Timer(0.1, timer)
						timer1.start()

						# LED発光用スレッド関数を処理,開始
						# 0.5秒毎にtimer_n2関数を呼び出し
						timer2 = threading.Timer(0.5, timer_n2)
						timer2.start()

						# ブザー用スレッド関数を処理,開始
						# 0.5秒毎にtimer_n3関数を呼び出し
						timer3 = threading.Timer(0.5, timer_n3)
						timer3.start()

						# ループを抜ける
						break

					# リセットボタン押下時
					elif g_button_r == True:
						print('\rボタンA押下でスタート、もう一度押下してください', end = '')

						# 1秒表示
						time.sleep(1)

						# カーソルを行頭へ移動
						# カーソル位置から行末まで消去
						sys.stdout.write("\033[2K\033[G")

						# バッファに溜まった文字列を出力し画面反映
						sys.stdout.flush()

						# リセットボタン状態をOFF
						g_button_r = False

# プログラムの処理状態:処理中の時
			elif status == 1:
				# ボタン押下状態:開始中の時
				if btn_status == True:
					# チャタリング対策に移行
					status = 2

					# 4桁7segLEDを発光させる
					Seven_segLED(counter)

				# ボタン押下状態:一時停止中の時
				elif btn_status == False:
					# チャタリング対策に移行
					status = 2

					# tcounter値を4桁7segLEDに発光させる
					Seven_segLED(tcounter)

				# リセットボタン押下時
				elif g_button_r == True:
					# チャタリング対策に移行
					status = 2

					# 4桁7segLEDに0を発光させる
					Seven_segLED(0)

# プログラムの状態:チャタリング対策状態の時
			elif status == 2:
				resume += 1
				if 5 <= resume:
					resume = 0
					status = 1

				# 一時停止中状態の時
				if btn_status == False:
					# tcounter値を4桁7segLEDに発光させる
					Seven_segLED(tcounter)

				# 開始状態の時
				elif btn_status == True:
					# 4桁7segLEDを発光させる
					Seven_segLED(counter)

			# ボタン押下状態を初期化
			g_button = False
			g_button_r = False

	except KeyboardInterrupt:
		# プログラム状態が初期状態の時
		# destroy関数は実行しない
		if status == 0:
			print('\nCtrl+cを押下')
			print('スレッド終了なし')

			# リソース解放
			GPIO.cleanup()

			print('プログラムを終了します。')
		else:
			destroy()

# Ctrl+c押下時実行
def destroy():
	global LedPin
	global BeepPin
	global timer1
	global timer2
	global timer3

	# モニターにプログラム終了メッセージを表示
	print('\nCtrl+cを押下,プログラムを終了します。')

	# タイマースレッドを中止
	print('\nスレッドを中止します。')

	# LEDを消灯
	print('LEDを消灯します。')
	GPIO.output(LedPin, GPIO.HIGH)

	# ブザーを切る
	print('ブザーを切ります。')
	GPIO.output(BeepPin, GPIO.HIGH)

	# リソース解放
	GPIO.cleanup()

	# スレッドを中止
	timer1.cancel()
	timer2.cancel()
	timer3.cancel()

	# 終了メッセージ
	print('終了します。')

if __name__ == '__main__':
	sys.exit(main())

