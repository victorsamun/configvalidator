# configchecker
Данный модуль позволяет выполнять валидацию конфигураций, загруженных с помощью `configparser`.

## Использование

1. Нужно инициализировать описание структуры валидной конфигурации:
   `schema = configchecker.ConfigSchema()`
2. Далее в описание нужно добавить информацию о возможных секциях.
   Сделать это можно с помощью вызова `schema.section`, который принимает валидатор названия секции и флаг «секция обязательная».
3. Затем в каждой секции аналогичным образом, вызовом `sect.value` описываются значения, содержащиеся в секции.

## Валидаторы имён/значений

Имеются базовые валидаторы:
* `ItemDefaultValidator` — всегда возвращает истину
* `ItemStringValidator` — проверяет совпадение строк с заданной (возможно, регистронезависимое)
* `ItemRegexValidator` — проверяет соответствие строки заданному регвыру
* `ItemNumberValidator` — проверяет, что строка явлется неотрицательным целым числом

И валидаторы-компоновщики, позволяющие собрать из базовых сложные проверки:
* `ItemNotValidator`, `ItemAndValidator`, `ItemOrValidator` — логика первого порядка над валидаторами
* `ItemCountValidator` — принимает на вход валидатор и функцию, проверяющую количество корректных срабатываний
   переданного валидатора (т.е. вернул `True`)

## Примеры использования

```python
import configparser
import configchecker as v

config = configparser.ConfigParser()
config.read_file("config")

schema = v.ConfigSchema()

# Секция с названием "REQUIRED" будет обязательной
with schema.section("REQUIRED") as s:
  # В ней обязательно должны быть ключи, соответствующие
  # регвыру r'item_\d+' и числовым значением и больше ничего
  s.value(v.ItemRegexValidator(r'item_\d+', value_val=v.ItemNumberValidator()).no_other()
  
# Секция с названием r'OPT_\w+' (проверка по регвыру) не обязательная
with schema.section(v.ItemRegexValidator(r'OPT_\w+'), required=False) as s:
  # И в ней может быть всё, что угодно
  pass
  
# Других секций нет
schema.no_other()

# Выполняем проверку
v.ConfigSchemaValidator(schema).validate(config)
```

Также, большое количество примеров можно найти в тестах (`test_configchecker.py`)


## Автор

Самунь Виктор, victor.samun@gmail.com
