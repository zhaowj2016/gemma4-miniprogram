/* BLOCK_SPEC_JSON
{"data":{"couponCardAmountText":"30 OFF","couponCardCondition":"Over 199","couponCardTitle":"New customer coupon","couponCardDate":"Valid for 7 days","couponCardButtonText":"Claim"},"methods":{"onCouponCardClaim":"function() { this.setData({ couponCardButtonText: 'Claimed' }); }"}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    couponCardAmountText: '30 OFF',
    couponCardCondition: 'Over 199',
    couponCardTitle: 'New customer coupon',
    couponCardDate: 'Valid for 7 days',
    couponCardButtonText: 'Claim'
  },
  onCouponCardClaim: function() {
    this.setData({ couponCardButtonText: 'Claimed' });
  }
});
