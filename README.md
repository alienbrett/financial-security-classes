# financial-security-classes
Pure python financial securities dataclasses, as foundation for other projects

## Examples

First set up and import the library
```python3
import datetime
import finsec as fs
```

## Create a currency
```python3
usd = fs.FiatCurrency(
    ticker = 'USD',
    nation = 'United States Dollar',
    gsid   = fs.GSID(20),
    identifiers = [
        fs.ISIN('abcdefg'),
    ],
)
```

## Create an index, denominated in USD
```python3
spx = fs.DerivedIndex(
    ticker = 'SPX',
    issuer = 'Standard & Poor',
    gsid   = fs.GSID(100),
    identifiers = [
        fs.FIGI('12345'),
    ],
    currency = usd,
)
```

## Create a few stocks
```python3
hyg = fs.ETP(
    ticker = 'HYG',
    gsid = fs.GSID(124),
    description = 'ISHARES IBOXX HIGH YLD CORP',
    primary_exc = fs.Exchange.NYSE,
    issuer      = 'ishares',
)
tsla = fs.Stock(
    ## Ticker will be auto-capitalized
    ticker = 'tSla',
    gsid = fs.GSID(125),
    description = 'Tesla corp',
    primary_exc = fs.Exchange.NYSE,
)

```

## Create a future, with SPX as underlier

```python3
esu22 = fs.NewFuture(
    gsid                = fs.GSID(120),
    ticker              = 'ESU22',
    underlying_security = spx,

    expiry_date         = datetime.date(2022,9,16),
    primary_exc         = fs.Exchange.CME,

    expiry_time_of_day  = fs.ExpiryTimeOfDay.OPEN,

    tick_size           = 0.25,
    multiplier          = 50.0,

    identifiers         = [
        fs.FIGI('234567'),
    ],

    #### This should be implied, since underlyer doesn't permit physical delivery
    # settlement_type     = fs.SettlementType.CASH,
    #### Without this argument, this should be set to UNKNOWN
    # expiry_series_type  = fs.ExpirySeriesType.MONTHLY,

)
```



To run tests:
```bash
$ python3.9 -m virtualenv venv
$ venv/bin/activate
$ make test
```
