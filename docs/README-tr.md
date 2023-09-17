<h1 align="center">
 babyagi

</h1>

# Diğer README çevirileri:
[<img title="عربي" alt="عربي" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/sa.svg" width="30">](docs/README-ar.md)
[<img title="Français" alt="Français" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/fr.svg" width="30">](docs/README-fr.md)
[<img title="Polski" alt="Polski" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/pl.svg" width="30">](docs/README-pl.md)
[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="30">](docs/README-pt-br.md)
[<img title="Romanian" alt="Romanian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ro.svg" width="30">](docs/README-ro.md)
[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="30">](docs/README-ru.md)
[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="30">](docs/README-si.md)
[<img title="Spanish" alt="Spanish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/es.svg" width="30">](docs/README-es.md)
[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="30">](docs/README-ua.md)
[<img title="简体中文" alt="Simplified Chinese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/cn.svg" width="30">](docs/README-cn.md)
[<img title="繁體中文 (Traditional Chinese)" alt="繁體中文 (Traditional Chinese)" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tw.svg" width="30">](docs/README-zh-tw.md)
[<img title="日本語" alt="日本語" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/jp.svg" width="30">](docs/README-ja.md)
[<img title="한국어" alt="한국어" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/kr.svg" width="30">](docs/README-ko.md)
[<img title="Magyar" alt="Magyar" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/hu.svg" width="30">](docs/README-hu.md)
[<img title="فارسی" alt="فارسی" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ir.svg" width="30">](docs/README-fa.md)
[<img title="German" alt="German" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/de.svg" width="30">](docs/README-de.md)
[<img title="Indian" alt="Indian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/in.svg" width="30">](docs/README-in.md)


# Kullanım
Bu Python scripti, LLM tabanlı task üretim ve yönetme sistemi odaklı bir çalışmadır. Sistem, istenen konu hakkında taskları oluşturmak, önceliklendirmek ve sorgulamak için OpenAI ve Pinecone API'lerini kullanır. Bu sistemin arkasındaki temel fikir, önceki görevlerin sonuçlarına ve önceden tanımlanmış bir hedefe dayalı görevler oluşturmasıdır. Komut dosyası daha sonra hedefe dayalı yeni görevler oluşturmak için OpenAI'nin doğal dil işleme (NLP) yeteneklerini ve bağlam için görev sonuçlarını depolamak ve almak için Pinecone'u kullanır. Bu çalışma, [BabyAGI-twitter.com](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (28 Mart 2023) paylaşımının basit bir kopyasıdır.

Bu README aşağıdakileri kapsayacaktır:

* [Nasıl çalışır](#nasil-calisir)

* [Nasıl kullanılır](#nasil-kullanilir)

* [Desteklenen Modeller](#desteklenen-modeller)

* [Döngüsel çalıştırma ile ilgili uyarı](#uyari)

# Nasıl Çalışır<a name="nasil-calisir"></a>

Script, aşağıdaki adımları gerçekleştiren sonsuz bir döngü çalıştırarak çalışır:

1. Görev listesinden ilk görevi çeker.
2. Görevi, ilk girdiye dayalı olarak görevi tamamlamak için OpenAI'nin API'sini kullanan yürütme aracısına gönderir.
3. Sonucu zenginleştirir ve Pinecone'da saklar.
4. Yeni görevler oluşturur ve önceki görevin amacına ve sonucuna göre görev listesini yeniden önceliklendirir.
execution_agent() işlevi, OpenAI API'nin kullanıldığı yerdir. İki parametre alır: amaç ve görev. Ardından OpenAI'nin API'sine görevin sonucunu döndüren bir bilgi istemi gönderir. İstem, AI sisteminin görevinin, amacının ve görevin kendisinin bir açıklamasından oluşur. Sonuç daha sonra bir dizi olarak döndürülür.

task_creation_agent() işlevi, önceki görevin amacına ve sonucuna dayalı olarak yeni görevler oluşturmak için OpenAI'nin API'sinin kullanıldığı yerdir. İşlev dört parametre alır: amaç, önceki görevin sonucu, görev açıklaması ve geçerli görev listesi. Ardından, OpenAI'nin API'sine yeni görevlerin bir listesini dizeler olarak döndüren bir bilgi istemi gönderir. İşlev daha sonra yeni görevleri, her bir sözlüğün görevin adını içerdiği bir sözlük listesi olarak döndürür.

Prioritization_agent() işlevi, görev listesini yeniden önceliklendirmek için OpenAI'nin API'sinin kullanıldığı yerdir. İşlev, geçerli görevin kimliği olan bir parametre alır. OpenAI'nin API'sine, yeniden önceliklendirilen görev listesini numaralı bir liste olarak döndüren bir bilgi istemi gönderir.

Son olarak, betik, bağlam için görev sonuçlarını depolamak ve almak için Pinecone'u kullanır. Komut dosyası, YOUR_TABLE_NAME değişkeninde belirtilen tablo adını temel alan bir Çam Kozası dizini oluşturur. Çam kozası daha sonra görevin sonuçlarını, görev adı ve herhangi bir ek meta veri ile birlikte dizinde depolamak için kullanılır.

# Nasıl Kullanılır<a name="nasil-kullanilir"></a>
Scripti kullanmak için şu adımları izlemeniz gerekir:

1. `git clone https://github.com/yoheinakajima/babyagi.git` ve `cd` aracılığıyla repoyu lokal bilgisayarınıza kopyalayın.
2. Gerekli paketleri kurun: `pip install -r requirements.txt`
3. .env.example dosyasını .env'ye kopyalayın: `cp .env.example .env`. Aşağıdaki değişkenleri ayarlayacağınız yer burasıdır.
4. OpenAI ve Pinecone API anahtarlarınızı OPENAI_API_KEY, OPENAPI_API_MODEL ve PINECONE_API_KEY değişkenlerinde ayarlayın.
5. PINECONE_ENVIRONMENT değişkeninde Pinecone ortamını ayarlayın.
6. TABLE_NAME değişkeninde görev sonuçlarının saklanacağı tablonun adını belirleyin.
7. (İsteğe bağlı) OBJECTIVE değişkeninde görev yönetimi sisteminin hedefini belirleyin.
8. (İsteğe bağlı) INITIAL_TASK değişkeninde sistemin ilk görevini ayarlayın.
9. Scripti çalıştırın.

# Desteklenen Modeller<a name="desteklenen-modeller"></a>

Bu script, tüm OpenAI modellerinin yanı sıra Llama.cpp aracılığıyla Llama modelleri ile de çalışmaktadır. Varsayılan olarak temelde çalışan model **gpt-3.5-turbo**'dur. Farklı bir model kullanmak için OPENAI_API_MODEL üzerinden model ismini belirtmeniz gerekmektedir.

## Lama kullanmak için

[Llama.cpp](https://github.com/ggerganov/llama.cpp) dosyasının en son sürümünü indirin ve oluşturmak için talimatları izleyiniz. Ek olarak, Llama model-weights dosyasına da ihtiyacınız olacaktır.

  - **Issues, discussions veya pull requests gibi bu reponun herhangi bir yerinde IPFS paylaşımı, magnet linkleri, yada diğer tüm model indirme bağlantılarını hiçbir şekilde paylaşmayınız. Hızlı bir şekilde silineceklerdir.**

Daha sonra `llama/main`i llama.cpp/main'e ve `models`i Lama model ağırlıklarının olduğu klasöre bağlayın. Ardından scripti `OPENAI_API_MODEL=llama` veya `-l` argümanı ile çalıştırın.

# Uyarı<a name="uyari"></a>
Bu komut dosyası, bir görev yönetim sisteminin parçası olarak sürekli olarak (for loop mantığı ile) çalıştırılmak üzere tasarlanmıştır. Bu komut dosyasının sürekli olarak çalıştırılması yüksek sayıda API request isteği kullanımına neden olabilir, bu nedenle lütfen kullanım sürenize dikkat ediniz. Ayrıca script, OpenAI ve Pinecone API'lerinin doğru şekilde kurulmasını gerektirir, bu nedenle betiği çalıştırmadan önce API'leri sırasıyla ve düzgün şekilde kurduğunuzdan emin olmanız tavsiye edilmektedir.

# Katkılarınız
BabyAGI henüz emekleme aşamasında olan bir çalışmadır ve bu nedenle hala ileri adımların belirlenmesine ihtiyaç duymaktadır. Şu anda, BabyAGI için en önemli hedefimiz, anlaşılması ve üzerine geliştirilmesi konusunda *basit* olmaktır. Bu sadeliği korumak için, PR'ları gönderirken aşağıdaki yönergelere uymanızı rica ederiz:
* Kapsamlı yeniden düzenleme yerine küçük, modüler değişikliklere odaklanın.
* Yeni özellikler eklerken, kullanım durumunu ayrıntılı bir açıklamasını sağlayın.

Ana geliştiricinin Twitter'dan paylaştığı güncelleme @yoheinakajima (Apr 5th, 2023):

> I know there are a growing number of PRs, appreciate your patience - as I am both new to GitHub/OpenSource, and did not plan my time availability accordingly this week. Re:direction, I've been torn on keeping it simple vs expanding - currently leaning towards keeping a core Baby AGI simple, and using this as a platform to support and promote different approaches to expanding this (eg. BabyAGIxLangchain as one direction). I believe there are various opinionated approaches that are worth exploring, and I see value in having a central place to compare and discuss. More updates coming shortly.

I am new to GitHub and open source, so please be patient as I learn to manage this project properly. I run a VC firm by day, so I will generally be checking PRs and issues at night after I get my kids down - which may not be every night. Open to the idea of bringing in support, will be updating this section soon (expectations, visions, etc). Talking to lots of people and learning - hang tight for updates!

# İlk zamanlar
BabyAGI, Twitter'da paylaşılan [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20)'nin (28 Mart 2023) sadeleştirilmiş bir sürümüdür. Reponun adı, orijinal otonom aracıya tepki olarak ortaya çıkmıştır ve ana geliştiricimiz, bunun bir AGI olduğunu tam anlamıyla iddia etmemektedir.

Bir VC olan [@yoheinakajima](https://twitter.com/yoheinakajima) tarafından sevgiyle yapılmıştır (ne inşa ettiğinizi görmek ister!)
