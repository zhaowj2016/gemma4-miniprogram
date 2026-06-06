/* BLOCK_SPEC_JSON
{"data":{"articleListTitle":"Latest articles","articleListItems":[{"id":"a1","title":"Designing stable blocks","desc":"Small semantic blocks reduce page generation failure points.","meta":"3 min read"},{"id":"a2","title":"Validator first workflow","desc":"Every composed page is checked before it leaves the harness.","meta":"5 min read"}]},"methods":{}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    articleListTitle: 'Latest articles',
    articleListItems: [
      { id: 'a1', title: 'Designing stable blocks', desc: 'Small semantic blocks reduce page generation failure points.', meta: '3 min read' },
      { id: 'a2', title: 'Validator first workflow', desc: 'Every composed page is checked before it leaves the harness.', meta: '5 min read' }
    ]
  }
});
