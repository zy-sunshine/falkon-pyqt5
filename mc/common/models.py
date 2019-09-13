import peewee

class AutoFillDbModel(peewee.Model):
    class Meta:
        db_table = 'autofill'
    id = peewee.AutoField(primary_key=True)
    server = peewee.TextField(index=True)
    data = peewee.TextField()
    password = peewee.TextField()
    username = peewee.TextField()
    lastUsed = peewee.IntegerField(default=0, db_column='last_used')

class AutoFillEncryptedDbModel(peewee.Model):
    class Meta:
        db_table = 'autofill_encrypted'
    id = peewee.AutoField(primary_key=True)
    server = peewee.TextField(index=True)
    data = peewee.TextField(db_column='data_encrypted')
    password = peewee.TextField(db_column='password_encrypted')
    username = peewee.TextField(db_column='username_encrypted')
    last_used = peewee.IntegerField(default=0)

class AutoFillExceptionsDbModel(peewee.Model):
    class Meta:
        db_table = 'autofill_exceptions'
    id = peewee.AutoField(primary_key=True)
    server = peewee.TextField(index=True)

class HistoryDbModel(peewee.Model):
    class Meta:
        db_table = 'history'
    id = peewee.AutoField(primary_key=True)
    url = peewee.TextField(unique=True)
    title = peewee.TextField(index=True)
    date = peewee.IntegerField(default=0)
    count = peewee.IntegerField(default=0)

class SearchEnginesDbModel(peewee.Model):
    class Meta:
        db_table = 'search_engines'
    id = peewee.AutoField(primary_key=True)
    name = peewee.TextField()
    url = peewee.TextField()
    icon = peewee.BlobField()
    shortchut = peewee.TextField()
    suggestionsUrl = peewee.TextField()
    suggestionsParameters = peewee.TextField()
    postData = peewee.TextField()

class IconsDbModel(peewee.Model):
    class Meta:
        db_table = 'icons'
    id = peewee.AutoField(primary_key=True)
    url = peewee.TextField(unique=True)
    icon = peewee.BlobField()

tables = [
    AutoFillDbModel,
    AutoFillEncryptedDbModel,
    AutoFillExceptionsDbModel,
    HistoryDbModel,
    SearchEnginesDbModel,
    IconsDbModel,
]
