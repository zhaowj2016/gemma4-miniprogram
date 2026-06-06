/* BLOCK_SPEC_JSON
{"data":{"productListTitle":"Recommended products","productListSubtitle":"Local mock","productListItems":[{"id":"p1","name":"Starter Kit","desc":"Core tools for a clean page.","priceText":"129.00"},{"id":"p2","name":"Growth Pack","desc":"Cards, forms, and actions.","priceText":"259.00"}]},"methods":{}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    productListTitle: 'Recommended products',
    productListSubtitle: 'Local mock',
    productListItems: [
      { id: 'p1', name: 'Starter Kit', desc: 'Core tools for a clean page.', priceText: '129.00' },
      { id: 'p2', name: 'Growth Pack', desc: 'Cards, forms, and actions.', priceText: '259.00' }
    ]
  }
});
