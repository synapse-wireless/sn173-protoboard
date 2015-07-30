ADMUX = 0x7c
ADCSRB = 0x7b
ADCSRA = 0x7a
ADCSRC = 0x77
ADCL = 0x78
ADCH = 0x79

def read_internal_temp():
    """ Read built-in temperature sensor """
    save_ADCSRA = peek(ADCSRA)
    save_ADCSRB = peek(ADCSRB)
    save_ADMUX = peek(ADMUX)
    save_ADCSRC = peek(ADCSRC)

    # Enable ADC
    # Clear ADATE, ADIE, and set prescaler to CPU Clk/32 = 500kHz
    my_ADCSRA = 0x95
    poke(ADCSRA, my_ADCSRA)     # enable ADC

    # Set channel and ref voltage
    poke(ADCSRB, 0x08)  # set MUX bit 5. Warning: have to set this before ADMUX
    poke(ADMUX, 0xc9)   # Set 1.6 Vref and MUX bits 0-4. MUX = 101001 (binary)

    # Set Tracking time
    poke(ADCSRC, 0x02)  # >=20us start-up time and 0 hold time required for reading temperature

    # Wait for bit 7 (AVDDOK) and bit 5 (REFOK) to go high.
    while (peek(ADCSRB) & 0xa0) != 0xa0:
        pass

    # Begin conversion
    poke(ADCSRA, my_ADCSRA | 0x40)

    # Wait for conversion to complete
    while (peek(ADCSRA) & 0x10) != 0x10:
        pass

    # Read ADC (LSB first)
    Lbyte = peek(ADCL)
    Hbyte = peek(ADCH)
    adc_value = Hbyte << 8 | Lbyte

    poke(ADCSRB, save_ADCSRB)
    poke(ADMUX, save_ADMUX)
    poke(ADCSRC, save_ADCSRC)
    poke(ADCSRA, save_ADCSRA)

    # Return degrees C
    return convert_to_dC(adc_value)

def convert_to_dC(adc_value):
    """ Convert raw temperature value to deci-degreesC (tenths of a degree Celcius)
        Accuracy within 0.1 degC of ideal datasheet formula and works from -70 to +147 degC
        which is bigger than full operating range of ATMega: -40 to +85 degC
    """
    return (adc_value - 275) * 339 / 30 + 380
