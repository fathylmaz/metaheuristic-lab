"""Algorithm catalog; ACO has its own discrete TSP laboratory."""
from .objectives import OBJECTIVES

ALGORITHMS = [
    ('fa', 'Ateşböceği Algoritması', 'Firefly Algorithm', 'Böcek ve sürü', 'Işığa bağlı çekicilik, rassal keşif', 'ready'),
    ('pso', 'Parçacık Sürü Optimizasyonu', 'Particle Swarm Optimization', 'Böcek ve sürü', 'Kişisel ve küresel en iyi konum', 'ready'),
    ('abc', 'Yapay Arı Kolonisi', 'Artificial Bee Colony', 'Böcek ve sürü', 'İşçi, gözlemci ve keşifçi arılar', 'ready'),
    ('aco', 'Karınca Kolonisi', 'Ant Colony Optimization', 'Böcek ve sürü', 'Feromon izleriyle ayrık rota arama', 'ready'),
    ('cs', 'Guguk Kuşu Arama', 'Cuckoo Search', 'Böcek ve sürü', 'Lévy uçuşları ve yuva değiştirme', 'ready'),
    ('mfo', 'Güve-Alev Optimizasyonu', 'Moth-Flame Optimization', 'Böcek ve sürü', 'Spiral yön bulma ve alev konumları', 'ready'),
    ('gwo', 'Gri Kurt Optimizasyonu', 'Grey Wolf Optimizer', 'Yırtıcı ve deniz', 'Alfa, beta ve delta hiyerarşisi', 'ready'),
    ('woa', 'Balina Optimizasyonu', 'Whale Optimization Algorithm', 'Yırtıcı ve deniz', 'Baloncuk ağı ve spiral kuşatma', 'ready'),
    ('ba', 'Yarasa Algoritması', 'Bat Algorithm', 'Yırtıcı ve deniz', 'Ekolokasyon, frekans, ses şiddeti ve darbe oranı', 'ready'),
    ('ssa', 'Salp Sürüsü', 'Salp Swarm Algorithm', 'Yırtıcı ve deniz', 'Lider-takipçi zincir hareketi', 'ready'),
    ('sma', 'Cıvık Mantar', 'Slime Mould Algorithm', 'Bitki ve biyoloji', 'Uyarlamalı ağırlık ve besin arayışı', 'ready'),
    ('iwo', 'İstilacı Yabani Ot', 'Invasive Weed Optimization', 'Bitki ve biyoloji', 'Uyarlamalı tohum üretimi, yayılım ve rekabetçi seçilim', 'ready'),
    ('sa', 'Tavlama Benzetimi', 'Simulated Annealing', 'Fizik ve evrim', 'Sıcaklığa bağlı çözüm kabulü', 'ready'),
    ('gsa', 'Yerçekimsel Arama', 'Gravitational Search Algorithm', 'Fizik ve evrim', 'Kütle ve çekim tabanlı hareket', 'ready'),
    ('de', 'Diferansiyel Evrim', 'Differential Evolution', 'Fizik ve evrim', 'Mutasyon, çaprazlama ve seçim', 'ready'),
]


def catalog() -> dict:
    return {
        'algorithms': [dict(zip(('id', 'name', 'english', 'category', 'description', 'status'), item)) for item in ALGORITHMS],
        'objectives': [
            {'id': obj.id, 'name': obj.name, 'description': obj.description, 'bounds': obj.bounds, 'optimum': obj.optimum}
            for obj in OBJECTIVES.values()
        ],
    }
