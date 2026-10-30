/*
 * FocusPix - firmware for the Arduino UNO Q (MCU side, STM32U585).
 *
 * Turns the UNO Q into a "focus beacon" display server:
 *   - 8x13 blue LED matrix  -> shows frames sent over the Router Bridge
 *   - onboard RGB LED 3     -> status colour (MCU pins PH10/11/12)
 *   - onboard RGB LED 4     -> secondary status (MCU pins PH13/14/15)
 *
 * The Pomodoro logic, weather fetch and rendering live in app/main.py on the
 * QRB2210 (MPU, Debian/Python). This sketch only exposes RPCs:
 *
 *   ping()                -> "pong"
 *   matrix_show(frame)    -> frame = 104 x '0'/'1', row-major 8 rows x 13 cols
 *   matrix_clear()        -> blanks the matrix
 *   rgb_set(led, r,g,b)   -> led 3 or 4, channels 0..255 (>=128 = on)
 *
 * RPCs are registered with provide_safe() so they run inside loop() via the
 * library's __loopHook() hook - no manual servicing of the bridge required.
 *
 * Frame layout (verified against the UNO Q pinout PDF, page "LED Matrix 8x13"
 * and the official "Arduino Logo" example in the UNO Q User Manual):
 *
 *   logo[row * 13 + col] = 0/1,  row 0 = top row, col 0 = left column
 *
 * Reference: https://docs.arduino.cc/tutorials/uno-q/user-manual/
 */

#include <Arduino_LED_Matrix.h>
#include <Arduino_RouterBridge.h>

ArduinoLEDMatrix matrix;

// Matrix size: 8 rows x 13 columns = 104 LEDs.
static constexpr uint8_t kRows = 8;
static constexpr uint8_t kCols = 13;
static constexpr uint16_t kFrameBits = kRows * kCols;

// RGB LED 3/4 via core variant macros (PH10-12 / PH13-15, MCU, 3.3 V).
// These are common-anode LEDs: a LOW output turns a channel on.
#define RGB3_R LED3_R
#define RGB3_G LED3_G
#define RGB3_B LED3_B
#define RGB4_R LED4_R
#define RGB4_G LED4_G
#define RGB4_B LED4_B
#define LED_ON LOW
#define LED_OFF HIGH

static const int kRgbPins[2][3] = {
    {RGB3_R, RGB3_G, RGB3_B},
    {RGB4_R, RGB4_G, RGB4_B},
};

static void self_test() {
  uint8_t logo[kFrameBits] = {0};

  // sweep: light every column in turn
  for (uint8_t c = 0; c < kCols; c++) {
    for (uint8_t r = 0; r < kRows; r++) {
      logo[r * kCols + c] = 1;
    }
    matrix.draw(logo);
    delay(60);
  }
  matrix.clear();
  delay(300);

  // checkerboard
  for (uint8_t r = 0; r < kRows; r++) {
    for (uint8_t c = 0; c < kCols; c++) {
      logo[r * kCols + c] = (r + c) % 2;
    }
  }
  matrix.draw(logo);
  delay(500);
  matrix.clear();

  // blink all four status LEDs - cycle R, G, B individually
  for (int i = 0; i < 3; i++) {
    // Red only
    for (int led = 0; led < 2; led++) {
      digitalWrite(kRgbPins[led][0], LED_ON);  // R channel
      digitalWrite(kRgbPins[led][1], LED_OFF); // G channel
      digitalWrite(kRgbPins[led][2], LED_OFF); // B channel
    }
    delay(200);
    for (int led = 0; led < 2; led++) {
      digitalWrite(kRgbPins[led][0], LED_OFF);
      digitalWrite(kRgbPins[led][1], LED_OFF);
      digitalWrite(kRgbPins[led][2], LED_OFF);
    }
    delay(200);
    // Green only
    for (int led = 0; led < 2; led++) {
      digitalWrite(kRgbPins[led][0], LED_OFF); // R channel
      digitalWrite(kRgbPins[led][1], LED_ON);  // G channel
      digitalWrite(kRgbPins[led][2], LED_OFF); // B channel
    }
    delay(200);
    for (int led = 0; led < 2; led++) {
      digitalWrite(kRgbPins[led][0], LED_OFF);
      digitalWrite(kRgbPins[led][1], LED_OFF);
      digitalWrite(kRgbPins[led][2], LED_OFF);
    }
    delay(200);
    // Blue only
    for (int led = 0; led < 2; led++) {
      digitalWrite(kRgbPins[led][0], LED_OFF); // R channel
      digitalWrite(kRgbPins[led][1], LED_OFF); // G channel
      digitalWrite(kRgbPins[led][2], LED_ON);   // B channel
    }
    delay(200);
    for (int led = 0; led < 2; led++) {
      digitalWrite(kRgbPins[led][0], LED_OFF);
      digitalWrite(kRgbPins[led][1], LED_OFF);
      digitalWrite(kRgbPins[led][2], LED_OFF);
    }
    delay(200);
  }
}

// ---------------------------------------------------------------- RPCs

String ping(String /*arg*/) { return "pong"; }

String matrix_show(String arg) {
  uint8_t logo[kFrameBits] = {0};

  const size_t len = arg.length();
  for (size_t i = 0; i < kFrameBits && i < len; i++) {
    if (arg.charAt(i) == '1') {
      logo[i] = 1;
    }
  }
  matrix.draw(logo);
  return "ok";
}

String matrix_clear(String /*arg*/) {
  matrix.clear();
  return "ok";
}

String rgb_set(int led, int r, int g, int b) {
  // led: 3 or 4 (0-based slot 0 or 1). Channels 0..255 (>=128 = on).
  if (led < 3 || led > 4) {
    return "ERR:led must be 3 or 4";
  }
  const int slot = led - 3;
  const uint8_t channels[3] = {(uint8_t)r, (uint8_t)g, (uint8_t)b};
  for (int ch = 0; ch < 3; ch++) {
    // The RGB LEDs are common-anode (active-low); >=128 = full brightness.
    digitalWrite(kRgbPins[slot][ch], channels[ch] >= 128 ? LED_ON : LED_OFF);
  }
  return "ok";
}

// ---------------------------------------------------------------- setup

void setup() {
  Serial.begin(115200);

  for (int led = 0; led < 2; led++) {
    for (int ch = 0; ch < 3; ch++) {
      pinMode(kRgbPins[led][ch], OUTPUT);
      digitalWrite(kRgbPins[led][ch], LED_OFF);
    }
  }

  matrix.begin();
  matrix.setGrayscaleBits(1);

  // Self-test before we block on the Router bridge handshake.
  self_test();

  Bridge.begin();
  Bridge.provide_safe("ping", ping);
  Bridge.provide_safe("matrix_show", matrix_show);
  Bridge.provide_safe("matrix_clear", matrix_clear);
  Bridge.provide_safe("rgb_set", rgb_set);

  Serial.println("FocusPix bridge ready");
}

void loop() {
  // provide_safe() callbacks are serviced automatically by __loopHook().
}
