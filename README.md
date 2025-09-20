# <img src="https://raw.githubusercontent.com/alienbrett/financial-security-classes/main/contract-icon.png" alt="FinSec icon" width="60"/> FinSec

[![codecov](https://codecov.io/gh/alienbrett/financial-security-classes/branch/main/graph/badge.svg?token=NEZT9SDMIU)](https://codecov.io/gh/alienbrett/financial-security-classes)
![open issues](https://img.shields.io/github/issues/alienbrett/financial-security-classes)
![pypi version](https://img.shields.io/pypi/v/financial-security-classes)
![license](https://img.shields.io/pypi/l/financial-security-classes)
![python version](https://img.shields.io/pypi/pyversions/financial-security-classes)

Pure python financial securities dataclasses, as foundation for other projects

## Install

```bash
## Install from pypi
pip install financial-security-classes

## or from the repo directly
git clone https://github.com/alienbrett/financial-security-classes
cd financial-security-classes
pip install -e .
```

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
amer_call = fs.American(
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

## Fixed Income

The `finsec.fixed_income_objs` module adds basic fixed–income building blocks:
**accrual schedules**, **legs**, **bonds**, and **OIS swaps**, with simple QuantLib interop.

> Requires `QuantLib` (Python bindings) at runtime for `as_quantlib*` helpers.

### Setup

```python3
import datetime, decimal
import finsec as fs
from finsec import fixed_income_objs as fio  # documented below
```

### Calendars, Day Count, and Periods

```python3
# Enumerations
fio.DayCount.Thirty360
fio.DayCount.Actual360
fio.DayCount.ActualActual

fio.BusinessDayConvention.unadjusted
fio.BusinessDayConvention.modified_following

# Market calendars
fio.Calendar.US_GovernmentBond
fio.Calendar.US_SOFR

# Relative/absolute periods
fio.Period(period='2d')   # 2 business days
'5y'                      # 5 years tenor wherever a tenor string is accepted
```

### Accruals & Schedules (`AccrualInfo`)

Create an accrual definition and inspect the generated schedule.

```python3
acc = fio.AccrualInfo(
    start=datetime.date(2025, 1, 1),
    end='3m',                   # or a concrete date
    period='1m',                # alternatively use freq=12 with a 1y end
    dc=fio.DayCount.Thirty360,
    front_stub_not_back=False,
)
len(acc)                        # number of coupon periods
acc.schedule().to_df()          # pandas DataFrame of period dates
```

### Rate Expressions (`FixedRate`)

```python3
expr = fio.FixedRate(rate=decimal.Decimal('0.05')) * (decimal.Decimal('1')/10) + 10
expr.get_fixing(None)           # -> Decimal('10.5')
expr.is_constant                # -> True
expr.model_dump()               # pydantic dict for serialization
```

### Coupon Leg (`Leg`)

```python3
fix_leg = fio.Leg(
    notional=1_000_000,
    cpn=fio.FixedRate(rate=decimal.Decimal('0.01')),  # 1% fixed
    acc=fio.AccrualInfo(
        start=datetime.date(2025, 1, 1),
        end=datetime.date(2026, 1, 1),
        dc=fio.DayCount.Thirty360,
        freq=12,  # monthly
        bdc=fio.BusinessDayConvention.unadjusted,
    ),
)
# fix_leg.schedule().to_df()
```

### Plain Vanilla Bond (`Bond`)

```python3
bond = fio.Bond(
    notional=1_000_000,
    leg=fix_leg,
    settle_days=1,              # settlement lag
)
ql_bond = bond.as_quantlib()    # QuantLib::Bond for pricing
# Round-trip JSON
bond2 = fio.Bond.model_validate_json(bond.model_dump_json())
```

### OIS Swap (fixed vs SOFR) (`Swap.make_ois`)

```python3
ois = fio.Swap.make_ois(
    start=datetime.date(2025, 1, 1),
    end='5y',
    rate=3.5 / 100,                 # fixed rate
    dc_fix=fio.DayCount.Actual360,
    dc_float=fio.DayCount.Actual360,
    freq_fix=1,
    freq_float=1,
    index='SOFR',
    cal_pay=fio.Calendar.US_SOFR,
    notional=1_000_000,
    pay_delay=fio.Period(period='2d'),
)
ois.model_dump()                     # inspect structure
```

### QuantLib Interop Helpers

* `obj.as_quantlib()` → the corresponding QuantLib instrument (e.g., `ql.Bond`).
* `bond.as_quantlib_helper()` → returns a `(Quote, Helper)` pair usable in curve bootstrapping.

> See `fixed_income.ipynb` for a minimal Treasury curve example (helpers from several fixed-rate bonds, then `ql.PiecewiseFlatForward`).

## Serialization support

Objects can be safely converted to json or dict format:

```python3
obj_json = fs.json_encode(euro_put)
obj_new = fs.json_decode(obj_json)
assert( obj_new == euro_put )

obj_dict = fs.dict_encode(euro_put)
obj_new = fs.dict_decode(obj_dict)
assert( obj_new == euro_put )
```


### Notes

* All objects are pydantic models; use `.model_dump()` / `.model_dump_json()` and `Class.model_validate_json()` for serialization.
* Tenor strings like `'2d'`, `'3m'`, `'5y'` are accepted where documented (periods, start/end).

## Run tests

To run tests:

```bash
$ python3.9 -m virtualenv venv
$ venv/bin/activate
$ make test
```
