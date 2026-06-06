/* BLOCK_SPEC_JSON
{"data":{"signupFormTitle":"Reserve a seat","signupFormDesc":"Form values stay local and mocked for validation.","signupFormName":"","signupFormPhone":"","signupFormNamePlaceholder":"Your name","signupFormPhonePlaceholder":"Phone number","signupFormButtonText":"Submit"},"methods":{"onSignupFormNameInput":"function(e) { this.setData({ signupFormName: e.detail.value }); }","onSignupFormPhoneInput":"function(e) { this.setData({ signupFormPhone: e.detail.value }); }","onSignupFormSubmit":"function() { this.setData({ signupFormButtonText: 'Submitted' }); }"}}
END_BLOCK_SPEC_JSON */
Page({
  data: {
    signupFormTitle: 'Reserve a seat',
    signupFormDesc: 'Form values stay local and mocked for validation.',
    signupFormName: '',
    signupFormPhone: '',
    signupFormNamePlaceholder: 'Your name',
    signupFormPhonePlaceholder: 'Phone number',
    signupFormButtonText: 'Submit'
  },
  onSignupFormNameInput: function(e) {
    this.setData({ signupFormName: e.detail.value });
  },
  onSignupFormPhoneInput: function(e) {
    this.setData({ signupFormPhone: e.detail.value });
  },
  onSignupFormSubmit: function() {
    this.setData({ signupFormButtonText: 'Submitted' });
  }
});
