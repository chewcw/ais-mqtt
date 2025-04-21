0x48 is the data type (this is 72 which is FFT)
0x0004072a is the data length, which is 263978₁₀ - Big Endian, total length - first 30 bytes (message header, topic name, etc.)
0x5aea8867000000 Little endian order, which is the timestamp.
0x00 is the FFT/OA calculation result status. 0=OK?
0x04 is the battery level, this 4 means 90% - 100%.
0x0751 is the ADC (average) - 28935₁₀, little endian?
0x0771 is the ADC (last) - 28935₁₀, little endian?
0x065c is the temperature. Little endian = 23558₁₀
0x4456753d is OA float value for ISO10816-3 x data, which is velocity mm/s. (Little endian)
0x445f553d is OA float value for ISO10816-3 y data, which is velocity mm/s. (Little endian)
0x2a3cb13d is OA float value for ISO10816-3 z data, which is velocity mm/s. (Little endian)
0x00002af5 is the ReportLen (10997₁₀ - big endian!) for single axis data volume. What is it? I believe is like this, the bytes are consecutively map?
0x55ad0b3f is frequency resolution. Equals to ~~1057729877₁₀ (Little endian)~~ or ~~1437403967₁₀(Big endian)~~, 0.5456136 (Little endian).
0x00006000 is the FFT length, equals to ~~6291456₁₀ (Little endian),~~ or 24576₁₀ (Big endian).
0x0000000000 is reserved bytes (5 bytes)








---

Basically, the FFT length
if sample_rate = 1000  # Hz
duration = 1        # seconds
N = sample_rate * duration  # Total number of samples (FFT length)

Then, to calculate frequency resolution
frequency_resolution = sample_rate / N
10997 x 4 = Total Acc(x);
10997 x 4 = Total Acc(y);
10997 x 4 = Total Acc(z);
10997 x 4 = Total Vec(x);
10997 x 4 = Total Vec(y);
10997 x 4 = Total Vec(z);



---

The relationship between Overall Amplitude (OA) and ISO 10816-3 is significant in the context of vibration monitoring for industrial machinery. 

- **Overall Amplitude (OA)** refers to the total vibration level measured, which can indicate the health of a machine. It is typically expressed in terms of velocity (e.g., mm/s or inches/sec).
- **ISO 10816-3** provides guidelines for evaluating vibration levels specifically for industrial machines with power above 15 kW and operating speeds between 120 and 15,000 RPM. This standard categorizes machines into different groups based on their size and power, outlining acceptable vibration levels for each group.
- The standard defines four zones of vibration severity: Zone A (green) for newly commissioned machines, Zone B (yellow) for unrestricted operation, Zone C (orange) for restricted operation, and Zone D (red) indicating potential damage. These zones help assess OA values against established thresholds to determine machine condition and maintenance needs.

In summary, OA is a critical measurement that is assessed using the criteria outlined in ISO 10816-3 to ensure the reliability and safety of industrial equipment.

---

Overall amplitude vibration measurement data typically includes readings from three axes: **X, Y, and Z**. Each axis corresponds to a different direction of vibration, allowing for a comprehensive analysis of mechanical movement. Here are the key points regarding these measurements:

- **X-Axis**: Measures lateral vibrations, indicating side-to-side movements.
- **Y-Axis**: Captures vertical vibrations, reflecting up-and-down motions.
- **Z-Axis**: Records axial vibrations, which represent forward and backward movements.

These measurements are crucial for diagnosing equipment health and identifying potential issues in rotating machinery. By analyzing the amplitude data from all three axes, engineers can obtain a complete picture of the vibration behavior and make informed maintenance decisions to prevent failures and optimize performance.

**`References:`**
[perplexityai](https://github.com/marketplace/perplexityai)
[Vibration Analysis: The Complete Guide](https://tractian.com/en/blog/vibration-analysis-complete-guide)
[Vibration spectrum analysis 101: Tips for getting started](https://www.plantservices.com/equipment/industrial-motors/article/33005617/vibration-spectrum-analysis-101-tips-for-getting-started)
[Fundamentals of Vibration - Technical Notes | DAEIL SYSTEMS](https://www.daeilsys.com/support/technical-notes/fundamentals-of-vibration/)
[Study of vibration](https://power-mi.com/content/study-vibration)
[Vibration Measurement: The Complete Guide](https://www.hbkworld.com/en/knowledge/resource-center/articles/measuring-vibration)
[Vibration Analysis Explained | Reliable Plant](https://www.reliableplant.com/vibration-analysis-31569)
[What are the Overall Vibration measurements and their use in Predictive Maintenance? - SenseGrow](https://www.sensegrow.com/blog/iot-solutions/overall-vibration-measurements)
[What is Vibration Analysis? | IBM](https://www.ibm.com/think/topics/vibration-analysis)
[Vibration - Measurement, Control and Standards](https://www.ccohs.ca/oshanswers/phys_agents/vibration/vibration_measure.html)
[What is Vibration Analysis and What is it Used For?](https://www.twi-global.com/technical-knowledge/faqs/vibration-analysis)
[Measurement of vibration - DMC](https://www.dmc.pt/en/medicao-de-vibracoes/)
[Vibration Measurements: Vibration Analysis Basics](https://blog.endaq.com/vibration-measurements-vibration-analysis-basics)

--------------------

fft_length: 24576
report_len: 11019
data_length: 264506
acc:
x: 11019
y: 11019
z: 11019
vec:
x: 11019
y: 11019
z: 11019
padded acc:
x: 24576
y: 24576
z: 24576
padded vec:
x: 24576
y: 24576
z: 24576

