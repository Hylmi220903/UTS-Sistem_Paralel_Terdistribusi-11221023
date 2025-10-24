Analisis Teoritis dan Prinsip Desain Sistem Agregator Log Berbasis Publish-Subscribe dalam Lingkungan Terdistribusi
Abstrak
Laporan ini menyajikan analisis mendalam mengenai prinsip-prinsip fundamental sistem terdistribusi yang diaplikasikan pada perancangan dan implementasi sebuah agregator log yang toleran terhadap kegagalan (fault-tolerant). Dengan memanfaatkan pola arsitektur Publish-Subscribe (Pub-Sub) sebagai fondasi, sistem ini dirancang untuk mencapai skalabilitas tinggi dan dekomposisi komponen (decoupling). Laporan ini secara sistematis mengupas tantangan-tantangan inti yang dihadapi, terutama dalam pengelolaan semantik pengiriman pesan, spesifiknya at-least-once delivery, yang secara inheren memperkenalkan risiko duplikasi data. Sebagai respons terhadap tantangan tersebut, diuraikan strategi mitigasi yang berpusat pada implementasi consumer yang bersifat idempoten (idempotent) dan mekanisme deduplikasi event yang kokoh. Analisis ini mensintesis riset akademis kontemporer dan teori sistem terdistribusi yang mapan untuk memberikan justifikasi teoretis yang kuat atas setiap keputusan arsitektural. Tujuannya adalah untuk mendemonstrasikan bagaimana kombinasi antara idempotency dan deduplikasi menjadi mekanisme krusial dalam mencapai konsistensi eventual (eventual consistency), memastikan integritas data log dalam sebuah lingkungan yang tidak dapat diandalkan dan terdistribusi secara inheren.

Bagian 1: Pendahuluan
1.1 Konteks: Ledakan Data Log di Era Cloud-Native
Lanskap rekayasa perangkat lunak modern telah mengalami pergeseran paradigma menuju arsitektur terdistribusi, yang dimanifestasikan melalui adopsi masif arsitektur layanan mikro (microservices), komputasi tanpa server (serverless), dan Internet of Things (IoT). Konsekuensi tak terhindarkan dari desentralisasi ini adalah peningkatan volume, kecepatan, dan variasi data log dan event secara eksponensial. Log tidak lagi berfungsi sekadar sebagai alat bantu debugging pasif, melainkan telah berevolusi menjadi aset strategis yang krusial untuk observability, intelijen bisnis, dan analisis keamanan. Dalam ekosistem yang terdekomposisi, kemampuan untuk mengagregasi, memproses, dan menganalisis data log dari ratusan atau bahkan ribuan sumber independen menjadi prasyarat fundamental untuk memahami kesehatan dan perilaku sistem secara holistik. Kebutuhan inilah yang mendorong urgensi perancangan sistem agregator log yang tidak hanya mampu menangani skala besar, tetapi juga andal dan konsisten.   

1.2 Arsitektur Publish-Subscribe sebagai Solusi Dominan
Sebagai jawaban atas tantangan agregasi data dalam skala besar, pola arsitektur Publish-Subscribe (Pub-Sub) telah muncul sebagai standar de facto. Arsitektur ini terdiri dari tiga komponen utama: Publisher (penerbit event), Subscriber (pelanggan event), dan Message Broker atau Topic (perantara). Keunggulan fundamental dari pola Pub-Sub adalah kemampuannya untuk menciptakan loose coupling (kopling longgar) antara komponen-komponen sistem. Publisher mengirimkan pesan ke sebuah topic tanpa perlu mengetahui identitas, lokasi, atau bahkan keberadaan Subscriber. Sebaliknya, Subscriber menerima pesan dari topic yang diminatinya tanpa mengetahui siapa Publisher-nya. Dekomposisi dalam ruang, waktu, dan sinkronisasi ini memungkinkan komponen untuk dikembangkan, di-deploy, dan diskalakan secara independen, menjadikannya fondasi arsitektural yang ideal untuk sistem agregator log di lingkungan terdistribusi.   

1.3 Tantangan Fundamental dalam Sistem Terdistribusi
Meskipun pola Pub-Sub menawarkan keuntungan signifikan, implementasinya dalam sistem terdistribusi mewarisi serangkaian tantangan yang kompleks dan inheren. Tantangan-tantangan ini, yang menjadi fokus utama laporan ini, meliputi:

Ketiadaan Jam Global (Lack of a Global Clock): Setiap node atau komponen dalam sistem memiliki persepsi waktunya sendiri, yang menyebabkan masalah dalam menentukan urutan kejadian (event ordering) secara global dan pasti.   

Kegagalan Parsial (Independent Failures): Komponen individual dapat mengalami kegagalan (misalnya, crash atau partisi jaringan) tanpa diketahui oleh komponen lain. Sistem harus dirancang untuk tetap beroperasi secara fungsional meskipun sebagian komponennya gagal, sebuah konsep yang dikenal sebagai toleransi kegagalan (fault tolerance).   

Kompleksitas Semantik Pengiriman Pesan: Menjamin bahwa sebuah pesan terkirim dan diproses dengan benar di tengah kegagalan jaringan dan komponen adalah masalah non-trivial, yang melahirkan berbagai model garansi pengiriman dengan trade-off yang berbeda.

Konsistensi Data: Mempertahankan keadaan yang konsisten di seluruh sistem menjadi sangat sulit ketika data direplikasi dan pembaruan terjadi secara asinkron. Teorema CAP (Konsistensi, Ketersediaan, Toleransi Partisi) secara formal mendefinisikan trade-off yang harus dihadapi dalam perancangan sistem ini.

1.4 Pernyataan Masalah dan Ruang Lingkup Laporan
Laporan ini bertujuan untuk menyediakan justifikasi teoretis yang komprehensif atas desain sebuah sistem agregator log yang tangguh terhadap duplikasi event dan kegagalan komponen. Fokus utama laporan ini bukanlah pada detail implementasi kode, melainkan pada analisis mendalam terhadap prinsip-prinsip yang mendasarinya. Secara spesifik, laporan ini akan mengupas tuntas konsep-konsep kunci yang menjadi tujuan pembelajaran (Bab 1–7), yaitu: karakteristik sistem terdistribusi, analisis komparatif arsitektur, semantik komunikasi, skema penamaan, pengurutan event, toleransi kegagalan, dan model konsistensi. Melalui analisis ini, akan ditunjukkan bagaimana implementasi idempotency dan deduplikasi dalam arsitektur Pub-Sub bukan sekadar pilihan teknis, melainkan strategi fundamental untuk mencapai keandalan dan konsistensi data dalam sistem terdistribusi.

Bagian 2: Analisis Teoritis Sistem Agregator Log Berbasis Publish-Subscribe
Bagian ini menyajikan analisis mendalam terhadap delapan pertanyaan teoretis (T1–T8) yang menjadi inti dari laporan ini. Setiap sub-bagian akan menguraikan konsep-konsep kunci, mengintegrasikan temuan dari literatur akademis, dan memberikan justifikasi atas keputusan desain yang relevan dengan sistem agregator log.

2.1 T1: Karakteristik dan Trade-Off Sistem Terdistribusi pada Arsitektur Pub-Sub (Bab 1)
Sistem terdistribusi, secara definisi, adalah kumpulan komponen otonom yang terhubung melalui jaringan dan berkolaborasi untuk menyelesaikan suatu tugas. Operasionalnya didasarkan pada tiga karakteristik fundamental yang membedakannya dari sistem monolitik:

Konkurensi (Concurrency): Beberapa proses atau komponen berjalan secara simultan dan independen, berinteraksi satu sama lain untuk mencapai tujuan bersama.

Ketiadaan Jam Global (Lack of a Global Clock): Tidak ada satu pun sumber waktu yang otoritatif dan sinkron di seluruh sistem. Setiap node memiliki jam lokalnya sendiri yang dapat mengalami drift, membuat penentuan urutan absolut dari event yang terjadi di node berbeda menjadi sebuah tantangan fundamental.   

Kegagalan Independen (Independent Failures): Kegagalan satu komponen tidak serta-merta menghentikan keseluruhan sistem. Sebaliknya, komponen lain mungkin tidak menyadari kegagalan tersebut dan terus beroperasi. Karakteristik ini menuntut perancangan mekanisme toleransi kegagalan yang canggih.   

Arsitektur Publish-Subscribe (Pub-Sub) secara inheren dirancang untuk beroperasi dalam lingkungan dengan karakteristik tersebut. Pola ini memperkenalkan atribut-atribut spesifik seperti kopling longgar (loose coupling), komunikasi asinkron, dan skalabilitas elastis. Loose coupling memungkinkan publisher dan subscriber untuk berevolusi dan diskalakan secara independen, yang merupakan prasyarat untuk sistem berskala besar.   

Namun, keuntungan ini datang dengan trade-off yang signifikan. Trade-off utama dalam arsitektur Pub-Sub adalah antara fleksibilitas dan skalabilitas versus kompleksitas operasional dan observability. Meskipun dekomposisi komponen sangat kuat, hal itu membuat status global sistem menjadi sulit untuk dipahami dan dilacak. Aliran data yang asinkron dan tidak langsung mempersulit proses debugging dan analisis kinerja end-to-end. Trade-off fundamental lainnya adalah yang dijelaskan oleh teorema CAP, yang memaksa arsitek untuk menyeimbangkan antara konsistensi, ketersediaan, dan toleransi partisi. Banyak sistem Pub-Sub, terutama yang dibangun di atas teknologi NoSQL, cenderung mengorbankan konsistensi kuat demi ketersediaan tinggi, mengadopsi model konsistensi eventual (BASE).   

Lebih jauh dari sekadar fitur teknis, "loose coupling" yang ditawarkan Pub-Sub pada dasarnya adalah sebuah strategi penskalaan organisasional. Dalam organisasi rekayasa perangkat lunak modern yang terdiri dari banyak tim kecil dan otonom, Pub-Sub memungkinkan setiap tim untuk mengembangkan dan men-deploy layanan mereka secara independen. Namun, kebebasan ini memindahkan titik integrasi dari panggilan API sinkron yang eksplisit ke kontrak data asinkron yang implisit, yaitu skema pesan dan nama topic. Tata kelola (governance) dari kontrak data ini menjadi sangat krusial. Kegagalan dalam mengelola skema ini dapat menyebabkan silent failures, di mana perubahan format oleh publisher menyebabkan serangkaian kegagalan di sisi consumer—sebuah masalah yang justru diperburuk oleh dekomposisi yang awalnya dicari.

Dalam konteks ini, sebuah agregator log dalam sistem Pub-Sub memainkan peran yang paradoksal. Ia merupakan sebuah upaya untuk mere-sentralisasi pengetahuan dalam sebuah sistem yang sengaja dirancang untuk terdesentralisasi. Sistem terdistribusi, khususnya yang menggunakan Pub-Sub, secara inheren menyebarkan informasi dan mempersulit penciptaan gambaran global yang koheren. Agregator log, dengan mengonsumsi, memproses, dan mengindeks event dari berbagai sumber yang terisolasi, menciptakan satu sumber kebenaran (single source of truth) yang dapat dikueri mengenai perilaku sistem. Dengan demikian, fungsi esensial dari agregator adalah untuk mengatasi tantangan utama yang diperkenalkan oleh arsitektur terdistribusi itu sendiri: hilangnya pandangan sistem yang tunggal dan terpadu.   

2.2 T2: Analisis Komparatif: Arsitektur Publish-Subscribe vs. Client-Server (Bab 2)
Pemilihan arsitektur komunikasi adalah salah satu keputusan paling fundamental dalam perancangan sistem. Dua pola yang dominan adalah Client-Server dan Publish-Subscribe.

Model Client-Server ditandai oleh komunikasi sinkron dengan pola request-response. Client secara eksplisit memulai permintaan ke alamat server yang spesifik dan dikenal, lalu menunggu respons. Pola ini menciptakan kopling yang erat (tight coupling): client dan server harus aktif secara bersamaan (temporal coupling), dan client harus mengetahui lokasi jaringan server (spatial coupling).   

Sebaliknya, model Publish-Subscribe didasarkan pada komunikasi asinkron yang dimediasi oleh broker. Publisher mengirimkan pesan ke topic tanpa pengetahuan tentang subscriber, dan sebaliknya. Ini menghasilkan kopling yang longgar (loose coupling), memisahkan komponen dalam ruang dan waktu.   

Arsitektur Pub-Sub menjadi pilihan yang superior untuk sistem agregator log karena alasan teknis berikut:

Skalabilitas Tinggi: Publisher (layanan yang menghasilkan log) dan subscriber (agregator log) dapat diskalakan secara independen. Jika volume log meningkat, hanya subscriber dan broker yang perlu ditingkatkan kapasitasnya, tanpa memengaruhi publisher.   

Resiliensi dan Toleransi Kegagalan: Jika agregator log (subscriber) mengalami downtime, broker akan menyimpan pesan dalam antrian. Ketika agregator kembali online, ia dapat memproses pesan-pesan yang tertunda, mencegah kehilangan data. Dalam model Client-Server, jika server log tidak tersedia, permintaan dari client akan gagal.

Komunikasi Satu-ke-Banyak (One-to-Many): Sebuah event log tunggal dapat dikonsumsi oleh beberapa subscriber yang berbeda (misalnya, satu untuk pengarsipan jangka panjang, satu untuk analisis real-time, dan satu lagi untuk sistem peringatan) tanpa perubahan pada sisi publisher.   

Integrasi Sistem Heterogen: Agregator log harus mampu menerima data dari berbagai layanan yang mungkin ditulis dalam bahasa pemrograman yang berbeda dan berjalan di platform yang berbeda. Pub-Sub menyediakan lapisan abstraksi universal melalui broker.   

Tabel berikut merangkum perbandingan kunci antara kedua arsitektur tersebut.

Tabel 2.1: Perbandingan Arsitektur Client-Server vs. Publish-Subscribe

Karakteristik	Model Client-Server	Model Publish-Subscribe
Pola Komunikasi	Sinkron, Request-Response	Asinkron, Berbasis Event
Kopling (Coupling)	Erat (spasial dan temporal)	Longgar (terdekopel dalam ruang dan waktu)
Skalabilitas	Terbatas; penskalaan server memengaruhi semua client.	Tinggi; publisher dan subscriber dapat diskalakan secara independen.
Toleransi Kegagalan (Temporal)	Rendah; server harus selalu tersedia saat client membuat permintaan.	Tinggi; broker bertindak sebagai penyangga (buffer) saat subscriber tidak tersedia.
Penemuan Layanan	Client harus mengetahui alamat server secara eksplisit.	Anonim; komponen hanya perlu mengetahui alamat broker/topic.
Kasus Penggunaan Khas	Panggilan API web (REST, gRPC), kueri basis data.	Agregasi log, streaming data, notifikasi, sistem event-driven.
Pada tingkat yang lebih fundamental, pilihan antara Client-Server dan Pub-Sub adalah pilihan tentang asumsi temporal sistem. Arsitektur Client-Server mengasumsikan dunia yang "berpusat pada sekarang" (now-centric), di mana interaksi terjadi secara sinkron dan instan. Sebaliknya, arsitektur Pub-Sub merangkul dunia yang "berpusat pada eventualitas" (eventually-centric), mengakui bahwa komponen beroperasi pada linimasa yang berbeda dan mungkin tidak selalu tersedia secara bersamaan. Sebuah agregator log, yang sifatnya harus menangani ledakan (bursty) log yang tidak terduga dari sumber-sumber yang tidak dapat diandalkan, secara inheren harus beroperasi di dunia yang eventually-centric ini. Mencoba memaksakan model Client-Server sinkron (misalnya, layanan logging dengan API REST) akan membebani publisher dengan keharusan mengimplementasikan logika buffering, retry, dan penanganan kegagalan yang kompleks—pada dasarnya, mereplikasi fitur-fitur yang sudah disediakan oleh message broker secara bawaan. Oleh karena itu, Pub-Sub bukan hanya pilihan yang "lebih baik", tetapi merupakan pilihan yang secara filosofis selaras dengan sifat masalah itu sendiri.

2.3 T3: Semantik Pengiriman Pesan dan Peran Krusial Idempotensi (Bab 3)
Dalam sistem terdistribusi, tidak ada jaminan bahwa pesan yang dikirim akan selalu sampai. Oleh karena itu, sistem perpesanan menawarkan berbagai tingkat garansi atau semantik pengiriman:

At-Most-Once: Sistem akan mencoba mengirim pesan satu kali. Pesan bisa hilang, tetapi tidak akan pernah terduplikasi. Ini adalah model "tembak dan lupakan" (fire-and-forget), cepat tetapi tidak andal. Cocok untuk kasus penggunaan di mana kehilangan data dapat ditoleransi, seperti metrik non-kritis.   

At-Least-Once: Sistem menjamin bahwa setiap pesan akan terkirim setidaknya satu kali. Tidak ada pesan yang hilang, tetapi pesan yang sama dapat terkirim lebih dari satu kali (duplikasi). Ini dicapai melalui mekanisme pengakuan (acknowledgement) dan pengiriman ulang (retry). Ini adalah pilihan pragmatis yang paling umum untuk sistem yang andal.   

Exactly-Once: Tingkat garansi tertinggi, di mana setiap pesan dijamin terkirim dan diproses tepat satu kali. Ini sangat sulit dan mahal untuk dicapai dalam sistem terdistribusi umum, sering kali memerlukan koordinasi transaksional yang kompleks antara broker, producer, dan consumer.   

Duplikasi dalam semantik at-least-once terjadi karena ketidakpastian. Seorang producer mengirim pesan dan menunggu acknowledgement (ack) dari broker. Jika producer tidak menerima ack dalam batas waktu tertentu (misalnya, karena ack hilang di jaringan, meskipun broker telah berhasil menyimpan pesan), producer akan mengasumsikan kegagalan dan mengirim ulang pesan yang sama. Dari perspektif consumer, ini akan terlihat sebagai dua pesan identik.   

Di sinilah idempotensi menjadi krusial. Idempotensi adalah properti dari sebuah operasi di mana menjalankannya beberapa kali menghasilkan efek yang sama seperti menjalankannya satu kali. Untuk sebuah agregator log, operasi pemrosesan yang idempoten berarti memproses event log yang sama berulang kali tidak akan mengubah status akhir di luar pemrosesan pertama. Misalnya, jika pemrosesan melibatkan penyimpanan log ke basis data, operasi tersebut harus dirancang untuk mengabaikan atau menimpa entri duplikat berdasarkan ID unik. Dengan membuat consumer idempoten, sistem dapat dengan aman mengadopsi semantik at-least-once—merangkul duplikasi di lapisan transpor—sambil tetap memastikan kebenaran dan integritas data di lapisan aplikasi.   

Penting untuk dicatat bahwa klaim "Exactly-Once Semantics" (EOS) dari beberapa platform, seperti Apache Kafka, sering kali disalahpahami. EOS di Kafka dicapai dengan menggabungkan operasi baca (dari topic sumber), pembaruan status, dan tulis (ke topic tujuan) ke dalam satu transaksi atomik. Ini bekerja dengan sangat baik untuk alur kerja pemrosesan aliran (stream processing) yang sepenuhnya berada di dalam ekosistem Kafka. Namun, tugas akhir dari sebuah agregator log sering kali adalah menulis data ke sistem eksternal, seperti Elasticsearch, basis data relasional, atau data warehouse. Penulisan ke sistem eksternal ini berada di luar batas transaksi Kafka. Sebuah kegagalan dapat terjadi setelah transaksi Kafka berhasil di-commit, tetapi sebelum penulisan ke basis data eksternal selesai. Saat consumer di-restart, ia akan memproses ulang pesan tersebut (karena offset Kafka belum di-commit secara permanen terkait dengan keberhasilan penulisan eksternal) dan mencoba lagi penulisan ke basis data. Tanpa idempotensi di sisi basis data (misalnya, menggunakan operasi UPSERT atau pemeriksaan kunci primer), duplikasi data akan terjadi di tujuan akhir. Dengan demikian, bahkan saat menggunakan broker dengan kapabilitas EOS, idempotensi di titik akhir sistem (system boundaries) tetap menjadi persyaratan yang tidak dapat ditawar.   

2.4 T4: Desain Skema Identifikasi Event untuk Deduplikasi yang Andal (Bab 4)
Mekanisme deduplikasi yang efektif bergantung sepenuhnya pada keberadaan pengenal unik per event (event_id) yang konsisten di setiap upaya pengiriman ulang. Consumer menggunakan event_id ini sebagai kunci untuk memeriksa apakah sebuah event telah diproses sebelumnya. Skema pembuatan event_id harus memenuhi dua kriteria utama: keunikan global dan resistensi terhadap tabrakan (collision-resistant).   

Beberapa strategi desain untuk event_id meliputi:

UUID (Universally Unique Identifier): UUID versi 4, yang didasarkan pada angka acak, adalah standar industri untuk memastikan keunikan dengan probabilitas tabrakan yang dapat diabaikan secara matematis. Ini adalah pilihan yang aman dan umum.

ULID (Universally Unique Lexicographically Sortable Identifier): Alternatif yang lebih modern yang menggabungkan timestamp presisi milidetik dengan komponen acak. Keunggulan utamanya adalah ULID dapat diurutkan secara leksikografis, yang berarti ID yang dibuat secara berurutan juga akan terurut berdasarkan waktu. Ini dapat meningkatkan kinerja pengindeksan di banyak basis data.

Kunci Komposit/Alami (Composite/Natural Key): Dalam beberapa kasus, ID unik dapat dibentuk dari kombinasi atribut-atribut dalam event itu sendiri, misalnya, dengan melakukan hashing pada user_id + transaction_id + timestamp. Ini adalah bentuk "idempotensi alami". Namun, pendekatan ini bisa rapuh; jika salah satu atribut sumber berubah, ID yang dihasilkan juga akan berubah, merusak kemampuan deduplikasi.   

event_id adalah kunci yang digunakan untuk melakukan lookup ke "penyimpanan deduplikasi" (deduplication store)—sebuah sistem penyimpanan persisten seperti Redis, DynamoDB, atau tabel basis data—yang mencatat semua event_id yang telah diproses. Keunikan, konsistensi, dan keberadaan event_id secara langsung menentukan efektivitas seluruh mekanisme deduplikasi. Kegagalan dalam menyediakan event_id yang konsisten akan menyebabkan deduplikasi gagal total, seperti yang diilustrasikan dalam kasus di mana event_id hilang atau tidak cocok antara event sisi peramban dan sisi server.   

Keputusan desain yang paling krusial terkait event_id adalah menentukan siapa yang bertanggung jawab untuk membuatnya. Lokasi pembuatan ID ini menentukan cakupan garansi deduplikasi. Pertimbangkan alur berikut: pengguna mengklik tombol, memicu panggilan ke layanan backend (producer), yang kemudian mempublikasikan event.

Skenario A (ID Dibuat oleh Producer): Layanan backend membuat event_id unik sebelum mempublikasikan event ke broker. Jika producer itu sendiri memiliki logika retry (misalnya, mencoba ulang publikasi yang gagal), ia akan menggunakan event_id yang sama pada setiap upaya. Ini memungkinkan consumer untuk menduplikasi event yang berasal dari retry di sisi producer. Ini adalah pendekatan yang paling kuat dan memberikan garansi end-to-end.

Skenario B (ID Dibuat oleh Broker): Jika message broker yang memberikan ID saat pesan diterima, maka dua upaya publikasi yang terpisah dari producer (karena retry) akan dianggap sebagai dua pesan yang berbeda oleh broker, masing-masing dengan ID uniknya sendiri. Skema ini tidak dapat mendeteksi duplikasi yang berasal dari producer.

Oleh karena itu, untuk mencapai deduplikasi end-to-end yang sejati, pengenal unik harus dibuat sedekat mungkin dengan sumber asli event dan harus bersifat immutable (tidak dapat diubah) sepanjang siklus hidupnya. Prinsip ini sejalan dengan rekomendasi untuk mengikat kunci idempotensi ke konteks transaksi logis, bukan sekadar ke panggilan fungsi teknis.   

2.5 T5: Manajemen Urutan Event (Ordering): Antara Totalitas dan Praktikalitas (Bab 5)
Pengurutan (ordering) event adalah salah satu masalah paling klasik dalam sistem terdistribusi. Terdapat dua model pengurutan utama:

Total Ordering: Semua event di seluruh sistem dapat ditempatkan dalam satu urutan sekuensial tunggal yang tidak ambigu, seolah-olah ada satu linimasa global. Mencapai ini sangat sulit dan mahal karena ketiadaan jam global dan memerlukan protokol konsensus yang kompleks (seperti Paxos atau Raft) yang dapat menjadi bottleneck kinerja.   

Partial (Causal) Ordering: Event hanya diurutkan jika ada hubungan sebab-akibat (causal relationship) di antara mereka. Relasi "terjadi-sebelum" (happens-before) yang diperkenalkan oleh Leslie Lamport mendefinisikan ini secara formal: event A terjadi sebelum event B jika A menyebabkan B (misalnya, pengiriman pesan dan penerimaannya). Event yang konkuren (tidak memiliki hubungan kausal) tidak memiliki urutan yang ditentukan satu sama lain. Jam logis (logical clocks) seperti Lamport Timestamps menyediakan pengurutan kausal ini.   

Untuk kasus penggunaan agregator log, memaksakan total ordering di semua event dari semua publisher yang berbeda sering kali tidak diperlukan dan kontra-produktif. Tidak ada signifikansi nyata apakah log dari layanan-A diproses sebelum atau sesudah log konkuren dari layanan-B. Yang jauh lebih penting adalah menjaga urutan event dari sumber yang sama (misalnya, urutan log yang dihasilkan oleh satu proses atau dalam konteks satu permintaan pengguna).

Pendekatan praktis yang efektif adalah dengan menggunakan kombinasi dari:

Timestamp berpresisi tinggi (misalnya, UTC dengan presisi mikrodetik) yang dibuat oleh publisher pada saat event terjadi.

Penghitung monotonik (monotonic counter) atau nomor urut (sequence number) yang unik dalam lingkup publisher tersebut.

Kombinasi (publisher_id, sequence_number) atau (timestamp, publisher_id) menyediakan urutan yang dapat diandalkan untuk event dari sumber yang sama. Ketika semua log diagregasi, mereka dapat diurutkan utamanya berdasarkan timestamp. Hubungan seri (ties) dapat dipecah secara arbitrer karena tidak ada hubungan kausal di antara event-event tersebut.

Pengejaran total ordering yang sempurna dalam konteks ini adalah bentuk optimasi prematur yang mengorbankan kinerja dan kesederhanaan untuk keuntungan praktis yang minimal. Kuncinya adalah mengidentifikasi garansi pengurutan apa yang sebenarnya dibutuhkan oleh kasus penggunaan hilir. Saat seorang pengembang melakukan debugging, mereka ingin melihat urutan kausal dari event dalam satu alur permintaan pengguna atau dalam satu proses. Mereka jarang perlu mengetahui apakah log dari proses yang tidak terkait terjadi beberapa nanodetik sebelum atau sesudah log lain. Pendekatan praktis (timestamp + counter) menyediakan jaminan yang "cukup baik" ini—yang memenuhi kebutuhan nyata pengguna—tanpa biaya komputasi dan latensi dari protokol konsensus yang diperlukan untuk total ordering yang ketat.

2.6 T6: Strategi Toleransi Kegagalan (Fault Tolerance) dan Mitigasi Risiko (Bab 6)
Sistem yang tangguh (resilient) bukanlah sistem yang tidak pernah gagal, melainkan sistem yang dapat mendeteksi, merespons, dan pulih dari kegagalan. Dalam arsitektur berbasis event seperti agregator log, mode kegagalan dapat dikategorikan ke dalam taksonomi berikut :   

Kesalahan Pengiriman (Delivery Errors): Pesan gagal mencapai tujuannya, baik dari publisher ke broker atau dari broker ke consumer. Ini bisa disebabkan oleh partisi jaringan, broker yang tidak tersedia, atau konfigurasi yang salah.

Kesalahan Pemrosesan (Processing Errors): Consumer berhasil menerima pesan tetapi gagal memprosesnya. Kesalahan ini dapat bersifat:

Transien (Transient): Kegagalan sementara yang kemungkinan akan berhasil jika dicoba lagi, misalnya, database hilir yang sementara tidak tersedia atau kegagalan jaringan sesaat.

Permanen (Permanent): Kegagalan yang tidak akan pernah berhasil tidak peduli berapa kali dicoba, misalnya, pesan dengan format data yang rusak (malformed), atau pelanggaran aturan bisnis yang tidak dapat diperbaiki. Pesan seperti ini sering disebut sebagai "poison pill".

Kegagalan Infrastruktur (Infrastructure Failures): Kegagalan pada lapisan dasar seperti crash pada node komputasi, kegagalan disk, atau masalah pada orkestrator kontainer.

Untuk setiap mode kegagalan, strategi mitigasi yang spesifik harus diterapkan.

Tabel 2.2: Pemetaan Mode Kegagalan dan Strategi Mitigasi

Mode Kegagalan	Deskripsi	Contoh	Strategi Mitigasi Utama
Kesalahan Pengiriman	Pesan hilang dalam perjalanan.	Publisher tidak dapat terhubung ke broker karena partisi jaringan.	Semantik pengiriman At-Least-Once dengan retry di sisi producer; Broker yang persisten dan bereplikasi.
Kesalahan Pemrosesan (Transien)	Kegagalan sementara di sisi consumer.	Basis data tujuan mengalami lock atau timeout sesaat.	Retry dengan Penundaan Eksponensial dan Jitter (Exponential Backoff with Jitter).
Kesalahan Pemrosesan (Permanent)	Pesan tidak dapat diproses secara fundamental.	Pesan JSON tidak valid atau berisi data yang melanggar constraint basis data.	Setelah beberapa kali retry gagal, pindahkan pesan ke Antrian Surat Mati (Dead Letter Queue - DLQ) untuk analisis manual.
Kegagalan Infrastruktur	Consumer atau komponen pendukungnya crash.	Proses consumer dihentikan secara tak terduga oleh orkestrator.	Consumer yang stateless atau dengan manajemen status eksternal; Penyimpanan Deduplikasi yang Tahan Lama (Durable Deduplication Store); Pengawasan dan restart otomatis oleh orkestrator.
Strategi Retry with Exponential Backoff and Jitter sangat penting untuk menangani kegagalan transien. Daripada mencoba ulang secara instan dan berulang-ulang (yang dapat memperburuk masalah), consumer menunggu dalam interval waktu yang meningkat secara eksponensial. Penambahan jitter (penundaan acak kecil) mencegah fenomena "kawanan guntur" (thundering herd), di mana banyak consumer mencoba ulang secara bersamaan setelah pemulihan layanan, yang dapat menyebabkan kegagalan sekunder.   

Untuk kegagalan permanen, Dead Letter Queue (DLQ) berfungsi sebagai jaring pengaman. Setelah batas retry tercapai, pesan "beracun" dipindahkan ke DLQ. Ini mencegah satu pesan buruk memblokir seluruh antrian pemrosesan. Tim operasional kemudian dapat memeriksa pesan di DLQ untuk mendiagnosis masalah, memperbaikinya, dan mungkin memproses ulang pesan tersebut secara manual, tanpa kehilangan data.   

2.7 T7: Pencapaian Konsistensi Eventual melalui Idempotensi dan Deduplikasi (Bab 7)
Konsistensi Eventual (Eventual Consistency) adalah model konsistensi yang menjamin bahwa, jika tidak ada pembaruan baru yang dilakukan pada suatu item data, semua akses ke item tersebut pada akhirnya akan mengembalikan nilai yang terakhir diperbarui. Model ini lebih mengutamakan ketersediaan (availability) daripada konsistensi yang kuat dan seketika, yang merupakan inti dari filosofi BASE (Basically Available, Soft state, Eventually consistent) yang banyak diadopsi oleh sistem NoSQL dan sistem terdistribusi skala besar.   

Dalam konteks agregator log, "keadaan konsisten" adalah koleksi log akhir yang telah disimpan, diindeks, dan bebas dari duplikasi. Selama periode latensi jaringan, retry consumer, atau pemrosesan yang tertunda, tampilan data log yang diagregasi mungkin untuk sementara waktu tidak lengkap atau bahkan mengandung duplikat. Namun, sistem dengan konsistensi eventual menjamin bahwa seiring berjalannya waktu, keadaan ini akan berkonvergensi ke representasi yang benar dan akurat.

Mekanisme untuk mencapai konvergensi ini adalah kombinasi dari idempotensi dan deduplikasi. Keduanya bekerja secara sinergis:

Sistem secara sadar menerima aliran input yang "kotor" dan tidak dapat diandalkan, yang penuh dengan potensi duplikasi akibat semantik pengiriman at-least-once.

Lapisan deduplikasi, yang menggunakan event_id unik, bertindak sebagai gerbang atau filter. Ia memeriksa setiap event yang masuk terhadap catatan event yang telah diproses. Jika event_id sudah pernah terlihat, event tersebut akan dibuang. Ini memastikan bahwa hanya event unik yang diizinkan untuk mengubah keadaan akhir sistem. Prinsip ini, yaitu menggunakan deduplikasi untuk memastikan integritas, adalah fundamental dalam sintesis data dari berbagai sumber.   

Logika pemrosesan yang idempoten bertindak sebagai lapisan pertahanan kedua. Jika karena suatu alasan (misalnya, kondisi balapan atau race condition di lapisan deduplikasi) event duplikat berhasil lolos, atau jika logika pemrosesan dijalankan ulang karena pemulihan dari kegagalan, sifat idempoten dari operasi tersebut (misalnya, UPSERT ke basis data) memastikan bahwa keadaan akhir tidak akan rusak.

Bersama-sama, idempotensi dan deduplikasi membentuk fondasi yang memungkinkan sistem untuk mengubah kekacauan dan ketidakandalan di lapisan transpor menjadi keteraturan dan kebenaran di lapisan penyimpanan data, sehingga mencapai konsistensi eventual.

Namun, ada nuansa praktis yang penting. Penyimpanan deduplikasi yang mencatat semua event_id tidak dapat tumbuh tanpa batas. Menyimpan setiap event_id selamanya akan menyebabkan kebocoran memori atau penyimpanan (storage leak) yang tidak berkelanjutan. Solusi praktisnya adalah dengan menetapkan Time-To-Live (TTL) pada setiap event_id yang disimpan. Pilihan durasi TTL ini (misalnya, 24 jam, 7 hari) adalah keputusan desain yang krusial. TTL harus cukup lama untuk menangani penundaan dan retry yang wajar dalam sistem, tetapi cukup pendek untuk menjaga sumber daya tetap terkendali. Ini berarti garansi konsistensi sistem tidaklah absolut; ia adalah "konsistensi eventual dalam jendela waktu yang terbatas". Ini adalah trade-off yang sadar antara kekuatan garansi konsistensi dan biaya operasional, sebuah detail penting yang sering diabaikan dalam diskusi teoretis murni.

2.8 T8: Metrik Kinerja Kunci dan Implikasinya pada Keputusan Desain (Bab 1-7)
Untuk mengevaluasi dan mengoptimalkan kinerja sistem agregator log, serangkaian metrik kunci harus dipantau secara terus-menerus. Metrik-metrik ini tidak hanya berfungsi sebagai indikator kesehatan sistem, tetapi juga secara langsung memengaruhi dan memvalidasi keputusan desain arsitektural.

Throughput: Mengukur kapasitas sistem, biasanya dalam satuan event per detik (EPS) atau megabita per detik (MB/s). Ini menunjukkan seberapa banyak beban yang dapat ditangani sistem sebelum kinerjanya menurun.   

Latency: Mengukur waktu yang dibutuhkan sebuah event untuk melewati sistem, dari saat dipublikasikan hingga saat tersedia untuk dikueri. Sangat penting untuk tidak hanya melihat latensi rata-rata, tetapi juga latensi ekor (tail latency), seperti persentil ke-95 (P 
95
​
 ) atau ke-99 (P 
99
​
 ). Tail latency mewakili pengalaman terburuk yang dialami oleh sebagian kecil permintaan dan sering kali merupakan indikator yang lebih baik dari masalah kinerja sistemik.   

Duplicate Rate: Persentase event duplikat yang diterima oleh consumer sebelum proses deduplikasi. Meskipun target di penyimpanan akhir adalah 0%, memantau tingkat duplikasi yang masuk dapat menjadi sinyal kesehatan jaringan dan publisher. Tingkat duplikasi yang tinggi secara tiba-tiba dapat mengindikasikan masalah di hulu.

Error Rate: Persentase event yang gagal diproses setelah semua upaya retry dan akhirnya berakhir di DLQ. Metrik ini mengukur keandalan logika pemrosesan dan kualitas data yang masuk.   

Metrik-metrik ini saling terkait dan sering kali berada dalam ketegangan, memaksa adanya trade-off dalam desain:

Kebutuhan Throughput Tinggi: Akan mendorong keputusan desain seperti pemrosesan batch di consumer. Mengambil 100 event sekaligus dari broker dan menyimpannya dalam satu transaksi basis data jauh lebih efisien daripada melakukannya satu per satu. Namun, ini akan meningkatkan latensi, karena event pertama dalam sebuah batch harus menunggu hingga batch penuh.

Kebutuhan Latensi Ekor Rendah: Akan mendorong keputusan sebaliknya: ukuran batch yang lebih kecil atau bahkan pemrosesan event tunggal. Ini juga menuntut penggunaan deduplication store yang sangat cepat (misalnya, basis data dalam memori seperti Redis) untuk meminimalkan penundaan pada setiap pemrosesan event. Analisis distribusi latensi, seperti skewness dan kurtosis, dapat mengidentifikasi apakah latensi yang tinggi disebabkan oleh outlier yang jarang atau masalah yang lebih sistemik.   

Garansi Zero Duplicate Rate yang Ketat: Memerlukan deduplication store yang persisten, sangat tersedia, dan mungkin transaksional. Ini menambah kompleksitas, biaya, dan latensi pada setiap operasi pemrosesan dibandingkan dengan sistem yang dapat mentolerir sedikit duplikasi.

Pada akhirnya, desain sistem adalah masalah optimisasi multi-dimensi. Tidak ada satu set parameter yang "benar" secara universal. Sebaliknya, keputusan desain, seperti ukuran batch consumer atau jenis deduplication store, harus didasarkan pada Service Level Objectives (SLOs) yang spesifik untuk kasus penggunaan tersebut. Sistem yang dirancang untuk peringatan keamanan real-time akan memprioritaskan latensi rendah di atas segalanya, sementara sistem untuk pengarsipan dan analisis batch akan memprioritaskan throughput tinggi dan biaya rendah. Metrik kinerja adalah alat yang memungkinkan arsitek untuk secara kuantitatif menalar tentang trade-off ini dan membuat keputusan yang terinformasi.

Bagian 3: Sintesis dan Kesimpulan
Analisis yang telah dipaparkan menunjukkan bahwa membangun sebuah sistem agregator log yang andal dan skalabel dalam lingkungan terdistribusi bukanlah hasil dari satu pilihan arsitektural tunggal, melainkan sebuah rangkaian keputusan desain yang saling terkait dan penuh dengan trade-off. Laporan ini telah menguraikan bagaimana prinsip-prinsip fundamental sistem terdistribusi—mulai dari karakteristik dasarnya hingga model konsistensi yang kompleks—secara langsung membentuk arsitektur sistem yang dirancang.

Argumen inti yang disajikan adalah sebagai berikut: cara paling pragmatis dan tangguh untuk membangun sistem pemrosesan data yang andal adalah dengan merangkul ketidakandalan yang inheren pada lapisan transpor jaringan dan secara strategis memindahkan beban penegakan kebenaran ke lapisan aplikasi. Dengan secara sadar memilih semantik pengiriman at-least-once, kita menerima bahwa duplikasi dan pengiriman ulang adalah kenormalan, bukan pengecualian. Sebagai gantinya, kita membangun pertahanan yang kokoh di tingkat aplikasi melalui dua pilar utama: idempotensi dan deduplikasi.

Idempotensi memastikan bahwa logika bisnis kita aman dari efek samping pemrosesan berulang.

Deduplikasi bertindak sebagai filter yang menjamin keunikan data yang masuk ke dalam keadaan akhir sistem.

Kombinasi kedua mekanisme ini memungkinkan sistem untuk mencapai konsistensi eventual: meskipun keadaan transien mungkin tidak konsisten karena kegagalan dan latensi, sistem dijamin akan berkonvergensi ke keadaan akhir yang benar dan bebas duplikasi.

Pada akhirnya, prinsip-prinsip yang dibahas—dekomposisi melalui Pub-Sub, pola toleransi kegagalan seperti retry dan DLQ, pendekatan praktis terhadap pengurutan event, dan desain yang digerakkan oleh metrik—tidaklah unik untuk agregator log. Prinsip-prinsip ini merupakan fondasi yang dapat digeneralisasi untuk hampir semua aplikasi terdistribusi modern yang intensif data, mulai dari platform e-commerce hingga sistem analitik real-time. Keberhasilan dalam membangun sistem semacam itu terletak pada pemahaman yang mendalam tentang trade-off yang ada dan kemampuan untuk merancang solusi yang secara eksplisit mengelola ketidakpastian, bukan mencoba untuk menghilangkannya.

Daftar Pustaka

M. van Steen and A.S. Tanenbaum, Distributed Systems, 4th ed., distributed-systems.net, 2023.

George Coulouris, G., Dollimore, J., Kindberg, T., Blair, G. (2011). Distributed Systems: Concepts and Design.

Al-Madani, B., Al-Roubaiey, A., & Baig, Z. A. (n.d.). Publish subscribe versus client server architecture. ResearchGate. Diakses dari https://www.researchgate.net/figure/Publish-subscribe-versus-client-server-architecture_fig1_259781956

Al-Zoubi, A. Y., Al-Masri, M. M., Al-Harahsheh, H. H., Al-Matahneh, S. A., & Al-Khatib, S. N. (2023). A systematic literature review on the performance comparison of SQL and NoSQL databases for big data analytics. Big Data and Cognitive Computing, 7(2), 97. https://doi.org/10.3390/bdcc7020097

Alahmadi, A. A., & Aljohani, M. (2024). De-duplication in evidence-based literature reviews: An opinion review. World Journal of Methodology, 14(1), 1-8. https://doi.org/10.5662/wjm.v14.i1.1

Anou, A., van Eyk, E., Toader, B. A., & Iosup, A. (2025). Investigating the overhead of distributed tracing on microservices and serverless applications. arXiv.

Ghadge, A. (2025). Building resilient systems: Error handling, retry mechanisms, and predictive analytics in event-driven architecture. ResearchGate. Diakses dari https://www.researchgate.net/publication/393462898_Building_Resilient_Systems_Error_Handling_Retry_Mechanisms_and_Predictive_Analytics_in_Event-Driven_Architecture

Katsaros, G., Gounaris, A., & Boumpouka, C. (2024). Advanced latency metrics for fault-tolerant services. arXiv. arXiv:2407.00015.

Lamport, L. (1978). Time, clocks, and the ordering of events in a distributed system. Communications of the ACM, 21(7), 558–565. https://doi.org/10.1145/359545.359563

Mishra, A. K., & Puthal, D. (2025). Ensuring exactly-once semantics in Kafka streaming systems. ResearchGate. Diakses dari https://www.researchgate.net/publication/395682231_Ensuring_Exactly-Once_Semantics_in_Kafka_Streaming_Systems

Schikuta, M. (2022). A unified logging library and architecture for improved observability in distributed information systems. Future Internet, 14(10), 274. https://doi.org/10.3390/fi14100274

Singh, A., Patra, A., Ghosh, S., & Pal, A. (2021). A study of distributed event streaming publish-subscribe systems. Term Project Report, CS60002, IIT Kharagpur. Diakses dari https://www.researchgate.net/publication/358106402_A_Study_of_Distributed_Event_Streaming_Publish-Subscribe_Systems

