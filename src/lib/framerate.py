from fractions import Fraction

def find_fraction(frame_rate, tolerance=0.01):
    # List of common frame rate fractions
    common_fractions = [
        (24000, 1001),
        (25000, 1001),
        (30000, 1001),
        (60000, 1001),
        (48000, 1001),
        (12000, 1001),
        (15000, 1001)
    ]

    # Check if frame rate matches any common fraction within tolerance
    for num, denom in common_fractions:
        if abs(frame_rate - (num / denom)) < tolerance:
            return Fraction(num, denom)

    # If no match is found, use the Fraction class to approximate
    frac = Fraction(frame_rate).limit_denominator(1001)  # Use a large limit for close approximation
    print(f"Approximated {frame_rate} to {frac}")
    return frac


if __name__ == "__main__":
    tests = [
        (23.976024, "24000/1001"),
        (23.98, "24000/1001"),
        (24.00, "24/1"),
        (24.98, "25000/1001"),
        (25.00, "25/1"),
        (29.97, "30000/1001"),
        (30.00, "30/1"),
        (59.94, "60000/1001"),
        (60.00, "60/1"),
        (120.00, "120/1"),
        (150.00, "150/1")
    ]

    for fr, expected in tests:
        fraction = find_fraction(fr)
        assert f'{fraction.numerator}/{fraction.denominator}' == expected, f"For frame rate {fr}, expected {expected}, got {fraction}"
    print("All tests passed!")

    fr = 23.976024
    fraction = find_fraction(fr)
    print(f"Fractional form of {fr} is approximately: {fraction}")
