// As-you-type formatting of sort codes
'use strict';

exports.SignUpChoices = {
  init: function () {
    var $form = $('.mtp-account-management__sign-up');
    if ($form.length !== 1) {
      return;
    }
    var $select = $form.find('select');
    var $hiddenInputs = $select.map(this.replaceSelect);
    $form.submit(function (e) {
      var someEmpty = false;
      $hiddenInputs.each(function () {
        var $input = $(this);
        if (!$input.val()) {
          $input.data('visualInput').addClass('form-control-error');
          someEmpty = true;
        }
      });
      if (someEmpty) {
        e.preventDefault();
        return false;
      }
      return true;
    });
  },

  replaceSelect: function () {
    var $select = $(this);
    var selectID = $select.attr('id');
    var initialValue = $select.val();
    var initialText = null;
    var choices = $select.find('option').map(function () {
      var $option = $(this);
      var value = $option.val();
      if (value) {
        var name = $option.text();
        if (initialValue === value) {
          initialText = name;
        }
        return {
          name: name,
          value: value
        };
      }
    }).get();
    var $visualInput = $('<input type="text" autocomplete="off" />');
    var $suggestions = $('<ul class="mtp-autocomplete-suggestions"></ul>');
    var $hiddenInput = $('<input type="hidden" />');
    $hiddenInput.data('visualInput', $visualInput);
    $visualInput.attr('class', $select.attr('class'));
    $hiddenInput.attr('name', $select.attr('name'));
    if (initialText) {
      $visualInput.val(initialText);
      $hiddenInput.val(initialValue);
    }
    $select.after($hiddenInput);
    $select.after($visualInput);
    $select.remove();
    $visualInput.attr('id', selectID);
    $visualInput.after($suggestions);
    $suggestions.attr('aria-controls', selectID);
    $suggestions.attr('aria-label', django.gettext('Suggestions'));
    $suggestions.hide();

    function getSearchTerm () {
      var searchTerm = $visualInput.val() || '';
      return $.trim(searchTerm.replace(/\s+/g, ' ')).toLowerCase();
    }

    var lastSearchTerm = getSearchTerm();

    function clearSuggestions () {
      $suggestions.empty();
      $suggestions.hide();
    }

    function setHiddenValue (value) {
      $hiddenInput.val(value);
      $hiddenInput.change();
    }

    $visualInput.on('change keyup', function () {
      var searchTerm = getSearchTerm();
      if (lastSearchTerm === searchTerm) {
        return;
      }
      lastSearchTerm = searchTerm;
      setHiddenValue('');
      clearSuggestions();
      if (searchTerm.length < 2) {
        return;
      }
      var suggestions = $.map(choices, function (choice) {
        if (choice.name.toLowerCase().indexOf(searchTerm) !== -1) {
          return choice;
        }
      });
      if (suggestions.length > 0 && suggestions.length <= 6) {
        $.each(suggestions, function () {
          var suggestion = this;
          var $suggestion = $('<a href="#"></a>');
          $suggestion.text(suggestion.name);
          $suggestion.click(function (e) {
            e.preventDefault();
            $visualInput.val(suggestion.name);
            setHiddenValue(suggestion.value);
            clearSuggestions();
            lastSearchTerm = getSearchTerm();
          });
          $suggestions.append($('<li></li>').append($suggestion));
        });
        $suggestions.show();
      }
    });

    $hiddenInput.on('change', function () {
      if ($hiddenInput.val()) {
        $visualInput.removeClass('form-control-error');
      } else {
        $visualInput.addClass('form-control-error');
      }
    });

    return $hiddenInput;
  }
};
