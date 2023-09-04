/// <reference path="../pb_data/types.d.ts" />
migrate((db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  collection.listRule = "@request.auth.id = user.id"

  return dao.saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("wlaeh3j9ukprvzt")

  collection.listRule = null

  return dao.saveCollection(collection)
})
