/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  collection.updateRule = ""

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  collection.updateRule = "@request.auth.id = user.id"

  return dao.saveCollection(collection)
})
