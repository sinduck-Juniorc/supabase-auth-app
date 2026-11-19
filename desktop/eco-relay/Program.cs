using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Web.Script.Serialization;
using Windows.Devices.Bluetooth.Advertisement;
using Windows.Storage.Streams;

// Windows is the origin and chooses among recently observed Android relays.
internal static class Program
{
    const ushort Company = 0xffff;
    const int FreshMs = 5000;
    static readonly Stopwatch Clock = Stopwatch.StartNew();
    static readonly Dictionary<uint, Candidate> Peers = new Dictionary<uint, Candidate>();
    static readonly Random Random = new Random();
    static readonly ManualResetEvent Stop = new ManualResetEvent(false);
    static readonly Model Quality = LoadModel();
    static volatile bool radioFailure;

    sealed class Model {
        public int selected_degree { get; set; }
        public Dictionary<string, double[]> cheb { get; set; }
    }
    static Model LoadModel() {
        using (var reader = new StreamReader(Assembly.GetExecutingAssembly().GetManifestResourceStream("quality.json")))
            return new JavaScriptSerializer().Deserialize<Model>(reader.ReadToEnd());
    }
    internal static double Score(double[] input) {
        double[] high = {-35, 1, 30, 5, 1, 1}, low = {-100, 0, 0, 0, 0, 0};
        var c = Quality.cheb[Quality.selected_degree.ToString()];
        var x = new double[6];
        double score = c[0];
        int offset = 1;
        for (int i = 0; i < x.Length; ++i) {
            x[i] = 2 * (Math.Max(low[i], Math.Min(high[i], input[i])) - low[i]) / (high[i] - low[i]) - 1;
            double b1 = 0, b2 = 0;
            for (int k = Quality.selected_degree - 1; k >= 0; --k) {
                double next = 2 * x[i] * b1 - b2 + c[offset + k];
                b2 = b1; b1 = next;
            }
            score += x[i] * b1 - b2;
            offset += Quality.selected_degree;
        }
        for (int i = 0; i < 6; ++i)
            for (int j = i + 1; j < 6; ++j) score += c[offset++] * x[i] * x[j];
        return Math.Max(0, Math.Min(1, score));
    }
    sealed class Candidate {
        internal uint Id;
        internal long Seen;
        internal int Rssi, Battery, Reception, Age;
        internal double QualityAt(long now) {
            return Score(new double[]{Rssi, Battery == 255 ? .2 : Battery / 100.0,
                Age + (now - Seen) / 1000.0, 1, Reception / 100.0, .1});
        }
    }
    static void Receive(BluetoothLEAdvertisementWatcher watcher, BluetoothLEAdvertisementReceivedEventArgs args) {
        foreach (var part in args.Advertisement.ManufacturerData) {
            if (part.CompanyId != Company || part.Data.Length != 12) continue;
            byte[] b = new byte[12];
            using (var reader = DataReader.FromBuffer(part.Data)) reader.ReadBytes(b);
            if (b[0] != 'Z' || b[1] != 'R' || b[2] != 1 || b[3] != 2 ||
                (b[8] > 100 && b[8] != 255) || b[10] > 100 || b[11] >= 5) continue;
            int sinkRssi = unchecked((sbyte)b[9]);
            if (sinkRssi > 0 || args.RawSignalStrengthInDBm > 0) continue;
            var peer = new Candidate {Id = BitConverter.ToUInt32(b, 4), Battery = b[8],
                Rssi = Math.Min((int)args.RawSignalStrengthInDBm, sinkRssi), Reception = b[10],
                Age = b[11], Seen = Clock.ElapsedMilliseconds};
            lock (Peers) Peers[peer.Id] = peer;
        }
    }
    static double[] Probabilities(int count, double best) {
        var weights = Enumerable.Range(1, count).Select(r => Math.Pow(r, -(1 + best))).ToArray();
        double total = weights.Sum();
        return weights.Select(w => .9 * w / total + .1 / count).ToArray();
    }
    static Candidate Choose() {
        long now = Clock.ElapsedMilliseconds;
        lock (Peers) {
            foreach (var p in Peers.Values.Where(p => now - p.Seen + 1000L * p.Age >= FreshMs).ToArray())
                Peers.Remove(p.Id);
            var ranked = Peers.Values.OrderByDescending(p => p.QualityAt(now)).ThenBy(p => p.Id).ToArray();
            if (ranked.Length == 0) return null;
            var probabilities = Probabilities(ranked.Length, ranked[0].QualityAt(now));
            double draw = Random.NextDouble();
            for (int i = 0; i < ranked.Length; ++i) {
                draw -= probabilities[i];
                if (draw < 0 || i + 1 == ranked.Length) {
                    Console.WriteLine("후보 {0} · 선택 {1:X8} · 품질 {2:F3} · 선택 확률 {3:P1}",
                        ranked.Length, ranked[i].Id, ranked[i].QualityAt(now), probabilities[i]);
                    return ranked[i];
                }
            }
            return null;
        }
    }
    static byte[] Input(uint target, uint session, uint seq) {
        using (var stream = new MemoryStream())
        using (var writer = new BinaryWriter(stream)) {
            writer.Write(new byte[]{90, 82, 1, 3}); writer.Write(target);
            writer.Write(session); writer.Write(seq); writer.Write((byte)(seq & 1));
            return stream.ToArray();
        }
    }
    static bool Advertise(byte[] data) {
        var publisher = new BluetoothLEAdvertisementPublisher();
        using (var writer = new DataWriter()) {
            writer.WriteBytes(data);
            publisher.Advertisement.ManufacturerData.Add(new BluetoothLEManufacturerData(Company, writer.DetachBuffer()));
        }
        publisher.Start();
        try {
            for (int i = 0; i < 30 && !Stop.WaitOne(100); ++i) {
                if (publisher.Status == BluetoothLEAdvertisementPublisherStatus.Started) {
                    Stop.WaitOne(1200);
                    return publisher.Status == BluetoothLEAdvertisementPublisherStatus.Started;
                }
                if (publisher.Status == BluetoothLEAdvertisementPublisherStatus.Aborted) break;
            }
            return false;
        } finally { publisher.Stop(); }
    }
    static int Main(string[] args) {
        if (args.SequenceEqual(new[]{"--self-test"})) {
            Console.WriteLine("{0:R} {1:R} {2}", Score(new double[]{-70,.8,2,1,.9,.1}),
                Probabilities(3, .6)[0], BitConverter.ToString(Input(1,2,3)));
            return 0;
        }
        try {
            var watcher = new BluetoothLEAdvertisementWatcher();
            watcher.Received += Receive;
            watcher.Stopped += (w, e) => {
                if (e.Error != Windows.Devices.Bluetooth.BluetoothError.Success) {
                    Console.Error.WriteLine("BLE 스캔 오류: " + e.Error); radioFailure = true; Stop.Set();
                }
            };
            Console.CancelKeyPress += (s, e) => { e.Cancel = true; Stop.Set(); };
            uint session = BitConverter.ToUInt32(Guid.NewGuid().ToByteArray(), 0), seq = 0;
            Console.WriteLine("R4를 발견한 스마트폰을 검색합니다. 종료는 Ctrl+C입니다.");
            watcher.Start();
            try {
                while (!Stop.WaitOne(2000)) {
                    var peer = Choose();
                    if (peer == null) { Console.WriteLine("중계 후보 대기"); continue; }
                    bool sent = Advertise(Input(peer.Id, session, seq));
                    if (!Stop.WaitOne(0))
                        Console.WriteLine("순번 {0} · 값 {1} · 로컬 광고 {2}", seq, seq & 1, sent ? "시작 확인" : "실패");
                    ++seq;
                }
            } finally { watcher.Stop(); }
            return radioFailure ? 1 : 0;
        } catch (Exception e) { Console.Error.WriteLine(e.Message); return 1; }
    }
}
