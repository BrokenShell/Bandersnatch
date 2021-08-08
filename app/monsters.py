import datetime

from Fortuna import TruffleShuffle, QuantumMonty, FlexCat
from Fortuna import canonical, percent_true, plus_or_minus

from app.monster_data import monsters_by_type


class Monster:
    type_options = set(monsters_by_type.keys())
    level_options = range(1, 21)
    rank_options = (
        "Rank 1",
        "Rank 2",
        "Rank 3",
        "Rank 4",
        "Rank 5",
    )
    random_type = TruffleShuffle(type_options)
    random_level = QuantumMonty(level_options).front_poisson
    random_rank = QuantumMonty(rank_options).front_linear
    random_name = FlexCat(
        monsters_by_type,
        key_bias="truffle_shuffle",
        val_bias="front_linear",
    )
    dice_lookup = dict(zip(rank_options, (4, 6, 8, 10, 12)))

    def __init__(self,
                 name=None,
                 monster_type=None,
                 level=None,
                 rank=None):
        self.type = monster_type or self.random_type()
        self.name = name or self.random_name(self.type)
        self.level = level or self.random_level()
        self.rank = rank or self.random_rank()
        self.damage = f"{self.level}d{self.dice_lookup[self.rank]}"
        self.health = self.random_resource()
        self.energy = self.random_resource()
        self.sanity = self.random_resource()
        self.time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def random_resource(self):
        alpha = canonical() if percent_true(50) else -canonical()
        beta = plus_or_minus(self.rank_options.index(self.rank))
        base_value = self.level * self.dice_lookup[self.rank]
        return round(base_value + beta + alpha, 2)

    def to_dict(self):
        return {
            "Name": self.name,
            "Type": self.type,
            "Level": self.level,
            "Rank": self.rank,
            "Damage": self.damage,
            "Health": self.health,
            "Energy": self.energy,
            "Sanity": self.sanity,
            "Time Stamp": self.time_stamp,
        }

    def __str__(self):
        return "\n".join(f"{key}: {val}" for key, val in self.to_dict().items()) + "\n"


# if __name__ == '__main__':
#     from time import sleep
#     from app.db_ops import DataBase
#
#     db = DataBase()
#     db.reset_db()
#     for _ in range(32):
#         db.insert_many(Monster().to_dict() for _ in range(32))
#         sleep(1)
