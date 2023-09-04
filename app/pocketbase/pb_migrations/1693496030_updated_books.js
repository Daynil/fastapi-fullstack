/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "khnf6qkw",
    "name": "user",
    "type": "relation",
    "required": false,
    "unique": false,
    "options": {
      "collectionId": "_pb_users_auth_",
      "cascadeDelete": false,
      "minSelect": null,
      "maxSelect": 1,
      "displayFields": []
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  // remove
  collection.schema.removeField("khnf6qkw")

  return dao.saveCollection(collection)
})
