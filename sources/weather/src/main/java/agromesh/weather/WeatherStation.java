package agromesh.weather;

import agromesh.Agro.DiscoveryRequest;
import agromesh.Agro.Reading;
import agromesh.Agro.SourceInfo;
import agromesh.Agro.SourceKind;
import agromesh.Agro.UdpPacket;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.MulticastSocket;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.Arrays;
import java.util.Collections;
import java.util.Random;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/** Fonte contínua: descoberta multicast e telemetria Protobuf via UDP. */
public final class WeatherStation {
    private final String id = env("SOURCE_ID", "estacao-01");
    private final String field = env("FIELD_ID", "sede");
    private final int interval = Integer.parseInt(env("INTERVAL_S", "3"));
    private final Random random = new Random();
    private final long start = System.nanoTime();
    private final DatagramSocket sender;
    private volatile InetSocketAddress gateway;

    private WeatherStation() throws SocketException {
        if (interval < 1) {
            throw new IllegalArgumentException("INTERVAL_S deve ser positivo");
        }
        sender = new DatagramSocket();
    }

    public static void main(String[] args) throws IOException {
        new WeatherStation().run();
    }

    private void run() throws IOException {
        String[] address = env("MCAST_ADDR", "239.255.10.1:9999").split(":");
        InetSocketAddress group = new InetSocketAddress(InetAddress.getByName(address[0]), Integer.parseInt(address[1]));
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        try (MulticastSocket receiver = joinGroup(group)) {
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                scheduler.shutdownNow();
                receiver.close();
                sender.close();
            }));
            scheduler.scheduleAtFixedRate(this::sendReading, interval, interval, TimeUnit.SECONDS);
            System.out.println("Estação " + id + " aguardando descoberta do gateway");
            listenDiscovery(receiver);
        } finally {
            scheduler.shutdownNow();
            sender.close();
        }
    }

    // Reutilização antes do bind permite compartilhar a porta com as fontes Python.
    private static MulticastSocket joinGroup(InetSocketAddress group) throws IOException {
        MulticastSocket receiver = new MulticastSocket(null);
        receiver.setReuseAddress(true);
        receiver.bind(new InetSocketAddress(group.getPort()));
        boolean joined = false;
        for (NetworkInterface network : Collections.list(NetworkInterface.getNetworkInterfaces())) {
            if (hasIpv4Multicast(network)) {
                receiver.joinGroup(group, network);
                joined = true;
            }
        }
        if (!joined) {
            receiver.close();
            throw new IOException("Nenhuma interface IPv4 disponível para multicast");
        }
        return receiver;
    }

    private static boolean hasIpv4Multicast(NetworkInterface network) throws SocketException {
        return network.isUp() && network.supportsMulticast()
                && Collections.list(network.getInetAddresses()).stream().anyMatch(a -> a instanceof Inet4Address);
    }

    private void listenDiscovery(MulticastSocket receiver) throws IOException {
        byte[] buffer = new byte[2048];
        while (!receiver.isClosed()) {
            DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
            receiver.receive(packet);
            try {
                onDiscovery(DiscoveryRequest.parseFrom(Arrays.copyOf(packet.getData(), packet.getLength())));
            } catch (IOException | IllegalArgumentException exc) {
                System.err.println("Descoberta inválida: " + exc.getMessage());
            }
        }
    }

    private void onDiscovery(DiscoveryRequest request) throws IOException {
        int port = request.getGatewayUdpPort();
        if (request.getGatewayIp().isBlank() || port < 1 || port > 65535) {
            return;
        }
        InetSocketAddress discovered = new InetSocketAddress(request.getGatewayIp(), port);
        if (!discovered.equals(gateway)) {
            System.out.println("Gateway descoberto em " + discovered.getHostString() + ":" + port);
        }
        gateway = discovered;
        send(UdpPacket.newBuilder().setAnnouncement(info()).build());
    }

    private void sendReading() {
        try {
            send(UdpPacket.newBuilder().setReading(sample()).build());
        } catch (IOException exc) {
            System.err.println("Envio UDP: " + exc.getMessage());
        }
    }

    private SourceInfo info() throws IOException {
        String advertised = System.getenv("ADVERTISE_IP");
        if (advertised == null || advertised.isBlank()) {
            // Um connect UDP escolhe a interface de saída sem enviar dados.
            try (DatagramSocket route = new DatagramSocket()) {
                route.connect(gateway);
                advertised = route.getLocalAddress().getHostAddress();
            }
        }
        return SourceInfo.newBuilder().setSourceId(id).setFieldId(field)
                .setKind(SourceKind.WEATHER_STATION).setIp(advertised)
                .setActive(true).setIntervalS(interval).build();
    }

    private Reading sample() {
        double phase = 2 * Math.PI * (System.nanoTime() - start) / 1e9 / 300;
        double temperature = 27 + 6 * Math.sin(phase) + random.nextGaussian() * 0.4;
        double humidity = Math.max(20, Math.min(100, 65 - (temperature - 27) * 3.5 + random.nextGaussian() * 1.5));
        double rain = random.nextDouble() < 0.05 ? random.nextDouble() * 4 : 0;
        return Reading.newBuilder().setSourceId(id).setFieldId(field).setKind(SourceKind.WEATHER_STATION)
                .setTimestampMs(System.currentTimeMillis())
                .putMetrics("temperature_c", round1(temperature))
                .putMetrics("air_humidity_pct", round1(humidity))
                .putMetrics("wind_kmh", round1(Math.abs(12 + random.nextGaussian() * 4)))
                .putMetrics("rain_mm", round1(rain)).build();
    }

    private void send(UdpPacket packet) throws IOException {
        InetSocketAddress destination = gateway;
        if (destination != null) {
            byte[] data = packet.toByteArray();
            sender.send(new DatagramPacket(data, data.length, destination));
        }
    }

    private static double round1(double value) {
        return Math.round(value * 10) / 10.0;
    }

    private static String env(String key, String fallback) {
        String value = System.getenv(key);
        return value == null || value.isBlank() ? fallback : value;
    }
}
