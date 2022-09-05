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

### Create a SPX future

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

### Options
The package supports americans and europeans:
```python3
amer_call = fs.European(
    gsid                = fs.GSID(1_234_567),
    underlying_security = tsla,
    callput             = 'call',
    strike              = 300.,
    expiry_date         = datetime.date(2022,12,16),
    expiry_time_of_day  = fs.ExpiryTimeOfDay.CLOSE,
    primary_exc         = fs.Exchange.CBOE,
    multiplier          = 100.0,
    identifiers         = [
        fs.FIGI('blahblahblah123'),
    ],
    settlement_type     = fs.SettlementType.PHYSICAL,
    
    # Without this argument, this set to fs.ExpirySeriesType.UNKNOWN
    expiry_series_type  = fs.ExpirySeriesType.MONTHLY,
)
```

And the european:
```python3
euro_put = fs.European(
    gsid                = fs.GSID(1_234_890),
    underlying_security = spx,
    callput             = 'put',
    strike              = 3_500,
    expiry_date         = '2022-12-30', # string expiries like this also supported
    expiry_time_of_day  = fs.ExpiryTimeOfDay.CLOSE,
    primary_exc         = fs.Exchange.CBOE, 
    expiry_series_type  = fs.ExpirySeriesType.QUARTERLY,
    multiplier          = 100.0,
    
    # Isn't strictly necessary, since this will be inferred from index underlying without physical delivery available
    settlement_type     = fs.SettlementType.CASH,
)
```


## Run tests
To run tests:
```bash
$ python3.9 -m virtualenv venv
$ venv/bin/activate
$ make test
```
