class IMUData:
    def __init__(self):
        self.x: list[float] = []
        self.y: list[float] = []
        self.z: list[float] = []
        self.t: list[float] = []
        self.region_idx = []

    def __len__(self):
        return len(self.x)

    def append(self, x: float = 0, y: float = 0, z: float = 0, t: float = None):
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        if t is None or t < 0:
            self.t.append(len(self.t) + 1)
        else:
            self.t.append(t)
            
