import pandas as pd

df = pd.read_csv("us_airports.csv")
regions = [
    (24, -125, 50.5, -66),   # contiguous US
    (51, -180, 72, -129),   # Alaska
    (18, -161, 23, -154),   # Hawaii
]

in_region = df.apply(
    lambda row: any(
        south <= row.latitude <= north and west <= row.longitude <= east
        for south, west, north, east in regions
    ),
    axis=1,
)

print(df.loc[~in_region, ["iata", "name", "city", "latitude", "longitude"]])