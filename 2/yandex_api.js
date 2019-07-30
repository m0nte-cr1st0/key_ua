ymaps.ready(init);

function init() {
  var geolocation = ymaps.geolocation;
  var city = '';
  geolocation.get({}).then(function (result) {
    city = result.geoObjects.get(0).properties.get('metaDataProperty.GeocoderMetaData.AddressDetails.Country.AdministrativeArea.SubAdministrativeArea.Locality.LocalityName')
    $('.city_yandex').text(city)
  })
}

window.onload = function() {
  $.ajax({
    type: 'GET',
    url: '{% url "location:get_city" %}',
    data: {city: $('.ml-auto > .city_yandex').text()},
    success: function(data) {
      if (!(window.location.pathname.includes(data.slug + '/'))) {
        if (window.location.pathname.length > 9) {
          history.pushState(null, null, window.location.pathname + data.slug + '/');
        } else {
          history.pushState(null, null, data.slug + '/');
        }
      }
      $('.city_yandex').text(city))
    },
    error: function(data) {
      $('html').html(data.template);
      $('.city_yandex').text(city))
    }
  })
}
