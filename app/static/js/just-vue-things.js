var app = new Vue({
  el: '#vueapp',
  data: {
    d: combined,
    urlTypes: ['direct_url', 'open_url', 'download_url', 'landing_url', 'other_url'],
    selectedFormat: 'html',
    possibleFormats: ['html','pdf', 'odt', 'docx', 'epub'],
    style: style,
  },
  delimiters: ['[[',']]'],
  methods: {
      containsKey: function(key, arr){
          var length = arr.length;
            for(var i = 0; i < length; i++) {
                for(var k of Object.keys(arr)) {
                  if(k == key) return true;
                }
            }
            return false;
      }

  },
  compiler: {
      whitespace: 'condense'
  }
});
