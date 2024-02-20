/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  // add
  collection.schema.addField(new SchemaField({
    "system": false,
    "id": "vgqfy1wh",
    "name": "location",
    "type": "relation",
    "required": false,
    "presentable": false,
    "unique": false,
    "options": {
      "collectionId": "seznitinqyrhxnl",
      "cascadeDelete": false,
      "minSelect": null,
      "maxSelect": 1,
      "displayFields": null
    }
  }))

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  // remove
  collection.schema.removeField("vgqfy1wh")

  return dao.saveCollection(collection)
})
