// States
// 

(function ($){
  window.numberArray = [],
  window.phoneNumber = '',
  window.updateDisplay,
  window.numberDisplayEl,
  window.inCallModeActive,
  window.dialpadButton = $('div#dialpad li'),
  window.dialpadCase = $('div#dialpad'),
  window.clearButton = $('#actions .clear'),
  window.callButton = $('#actions .call'),
  window.actionButtons = $('#actions'),
  window.backButton = $('#actions .back'),
  window.numberDisplayEl = $('#numberDisplay input');

  function compilePhoneNumber(numberArray){
    if (window.numberArray.length > 1){ 
      window.phoneNumber = window.numberArray.join('');
    } else {
      window.phoneNumber = window.numberArray
    }
    return this.phoneNumber;
  };

  function updateDisplay(phoneNumber){
    window.numberDisplayEl.val(window.phoneNumber);
  };

  function clearPhoneNumber(){
    window.numberDisplayEl.val(window.numberDisplayEl.val().slice(0, -1));
    window.phoneNumber = window.phoneNumber.slice(0, -1);
    window.numberArray.pop();
  };

  function disableInCallInterface(){
    removeReadOnlyInput();
    enableCallButton();
    window.inCallModeActive = false;
  }

  function enableCallButton(){
    window.callButton.removeClass('deactive');
  };

  function enableDialButton(){
    window.dialpadCase.removeClass('deactive');
  };

  function removeReadOnlyInput(){
    window.numberDisplayEl.removeAttr('readonly');
  }

  function refreshInputArray(){
    this.numberDisplayElContent = window.numberDisplayEl.val(); 
    window.numberArray = this.numberDisplayElContent.split('');
  };

  window.dialpadButton.click(function(){
	  if(( window.phoneNumber.length > 8 && window.phoneNumber.startsWith('06'))
		  || window.phoneNumber.length > 10 && window.phoneNumber.startsWith('382')){
		  return;
	  }
		  
    if( !$(dialpadCase).hasClass('deactive') ){
      var content = $(this).html();
	  if(window.phoneNumber.length == 0 && (content != 3 && content != 0)){
		return;
	  }
      refreshInputArray();
      window.numberArray.push(content);
      compilePhoneNumber();
      updateDisplay();
      checkDisplayEl();
      saveNumberDisplayEl();
    }
  });


  function checkDisplayEl(){
	  if( window.phoneNumber.length > 0 ){
		  addReadyToClear();
	  }
    if(( window.phoneNumber.length > 8 && window.phoneNumber.startsWith('06'))
		  || window.phoneNumber.length > 10 && window.phoneNumber.startsWith('382')){
      addReadyToClear();
      addReadyToCall();
      enableActionButtons();
    } else if ( window.numberDisplayEl.val() == "" ) {
      removeReadyFromClear();
      removeReadyFromCall();
      disableActionButtons();
    } else if ( ( window.phoneNumber.length <= 8 && window.phoneNumber.startsWith('06'))
		  || window.phoneNumber.length <= 10 && window.phoneNumber.startsWith('382') ) {
		removeReadyFromCall();
	}
  }

  function disableActionButtons(){
    window.actionButtons.addClass('deactive');
  }

  function enableActionButtons(){
    window.actionButtons.removeClass('deactive');
  }

  function addReadyToCall(){
    window.callButton.addClass('ready');
  }

  function removeReadyFromCall(){
    window.callButton.removeClass('ready');
  }

  function addReadyToClear(){
    window.clearButton.addClass('ready');
  }

  function removeReadyFromClear(){
    window.clearButton.removeClass('ready');
  }

  function saveNumberDisplayEl(){
    lastNumberDisplayEl = window.numberDisplayEl.val()
  }

  function displayLastSavedNumberDisplayEl(){
    console.log('Last displayed element value: ' + lastNumberDisplayEl);
  }

  $('div#actions li.clear').click(function(){
	  if(window.phoneNumber.length){
		enableCallButton();
		enableDialButton();
		clearPhoneNumber();
		removeReadOnlyInput();
		updateDisplay();
		checkDisplayEl();
		disableInCallInterface();
	  }
  });

  $('div#actions li.call').click(function(){
	  if(window.phoneNumber.length > 8) {
		location.href = "./charge.html?provider=montel&num=" + phoneNumber;
	  }
  });

  $('div#actions li.back').click(function(){
	$.ajax({
	  url: "http://127.0.0.1:8080/notes",
	  cache: false,
	  success: function(html){
		if(html == "0"){
			location.href = "./index.html";
		}
	  }
	}); 
  });

})(jQuery);