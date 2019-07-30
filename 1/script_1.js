function inc(el, v){
  var i = $(el.parentNode).find("input");;
  var max_ = +$(i).attr('data-max');
  var min_ = +$(i).attr('data-min');

  i.val((+i.val() + +v))


  if (!(i.val() % min_ == 0)) {
    i.val(Math.round(i.val() / min_) * min_)
  }
  if (+i.val() >= max_) {
    i.val(max_)
  } else if (+i.val() < min_) {
    i.val(0)
  }

  var spec = $('.spec')
  var numbers = $(spec).find('.sp_n');
  var prices = $(spec).find('.sp_p');
  var numberList = [];
  var priceList = [];
  var inp = $('.numerator > input')
  var curr_rate = +$(inp).attr('data-curr_rate')

  for (var j = 0; j < numbers.length; j++){
    numberList.push(+$(numbers[j]).text())
    priceList.push(+$(prices[j]).text() / curr_rate)
  };

  if (Math.max(...numberList) <= +$(inp).val()) {
    if (numberList.length) {
      $(".sp_price").text(priceList[numberList.indexOf(Math.max(...numberList))])
      $(".value.data-price").text(priceList[numberList.indexOf(Math.max(...numberList))])
    } else {
      $(".sp_price").text($(inp).attr('data-product_price') / curr_rate)
      $(".value.data-price").text($(inp).attr('data-product_price') / curr_rate)
    }
  } else {
    if (+$(inp).val() == +$(inp).attr('data-min')) {
      $(".sp_price").text($('.add_to_cart').attr('data-price') / curr_rate);
      $(".value.data-price").text($('.add_to_cart').attr('data-price') / curr_rate);
    } else if (+$(inp).val() < +$(inp).attr('data-min')) {
      $(".sp_price").text(0);
      $(".value.data-price").text(0)
    } else {
      for (var j = 0; j < numberList.length; j++) {
        if (numberList[j] >= +$(inp).val()) {
          if (j == 0) {
            if (min_ <= +$(inp).val() && +$(inp).val() <= numberList[j]){
              $(".sp_price").text($('.add_to_cart').attr('data-price') / curr_rate);
              $(".value.data-price").text($('.add_to_cart').attr('data-price') / curr_rate);
              break
            } else {
              $(".sp_price").text(priceList[numberList.indexOf(numberList[j])]);
              $(".value.data-price").text(priceList[numberList.indexOf(numberList[j])])
              break
            }
          }
          $(".sp_price").text(priceList[numberList.indexOf(numberList[j])-1]);
          $(".value.data-price").text(priceList[numberList.indexOf(numberList[j])-1])
          break
        }
      }
    }
  }

  var counts = $('input[type="number"].field')
  var total = 0;
  for (var j=0; j<counts.length; j++) {
      var product_price = $((counts[j]).parentNode).find(".sp_price").text();
      total += +(counts[j].value * product_price / min_).toFixed(2);
  }
  
