var LAST_STEP = 9;
var completedStep = undefined;
var currentStep = undefined;
var seenStep = undefined;


function updateState(data) {
    completedStep = data['completed_step'];
    currentStep = data['current_step'];
    seenStep = data['seen_step'];
}

function navigateToTop() {
    document.body.scrollTop = 0; // For Chrome, Safari and Opera
    document.documentElement.scrollTop = 0; // For IE and Firefox
}

function activateTab() {
    $('[data-target]').removeClass('active');
    $('[data-target="#step' + currentStep + '"]').addClass('active');
    $('.tab-pane').removeClass('active');
    $('#tab' + currentStep).addClass('active');
}

function setNavigationStepClass(step) {
    var allClasses = 'wizard-tab-done wizard-tab-seen';
    if (step == currentStep) {
        return
    }
    var stepSpan = $(('span.step-' + step));
    stepSpan.removeClass(allClasses);
    if (step == seenStep && step != completedStep) {
        stepSpan.addClass('wizard-tab-seen');
    } else if (step <= completedStep) {
        stepSpan.addClass('wizard-tab-seen');
        stepSpan.addClass('wizard-tab-done');
    }
}

function resetAllButtons() {
    $('button[data-loading-text]').button('reset');
    $('.qs-action-button').removeClass('btn-success').addClass('btn-primary');
}

function refreshNavigationSteps() {
    for (var step = 1; step <= LAST_STEP; step++) {
        setNavigationStepClass(step);
    }
}

function changeNextButtonState() {
    if (currentStep === LAST_STEP || currentStep == 1) {
        $('#linkToNextStep').hide();
    } else {
        $('#linkToNextStep').show();
        if (completedStep >= currentStep) {
            $('#linkToNextStep').attr('disabled', false);
        } else {
            $('#linkToNextStep').attr('disabled', true);
        }
    }
}

function changePrevButtonState() {
    if (currentStep === 1) {
        $('#linkToPreviousStep').hide();
    } else {
        $('#linkToPreviousStep').show();
    }
}

function moveToStep(step) {
    if (step <= completedStep + 1) {
        $.post('/step', JSON.stringify({step: step}), function(data) {
            updateState(data);
            activateTab();
            changeNextButtonState();
            changePrevButtonState();
            refreshNavigationSteps();
            navigateToTop();
            resetAllButtons();
            resetErrorBox();
        });
    }
}

function registerLoadingButton(buttonId, endpoint, successMessage) {
    $(buttonId).click(function () {
        var btn = $(this);
        resetErrorBox();
        btn.button('loading');
        $.post(endpoint, function (data) {
            updateState(data);
            changeNextButtonState();
            btn.text(successMessage);
            btn.removeClass('btn-primary').addClass('btn-success');
        }).fail(function(xhr){
            btn.button('reset');
            updateErrorBox(xhr);
            btn.removeClass('btn-primary').addClass('btn-danger');
        });
    });
}

function showAlert(classSelector) {
    $(classSelector).removeClass("in").show();
    $(classSelector).delay(200).addClass("in").fadeOut(4000);
}

function updateErrorBox(xhr) {
  var errorMessage = 'Internal error';
  if (xhr.status === 504) {
      errorMessage = 'Request timed out';
  }
  if (xhr.status === 400) {
      data = JSON.parse(xhr.responseText);
      errorMessage = data.message;
      $('.errorDetails').css({display: "block"});
      $('.exceptionName').text(data.exception);
      $('.exceptionDescription').text(data.description);
      $('.exceptionTraceback').text(data.traceback);
      $('.errorDetails').css({display: "block"});
      $('.collapse').collapse('hide');
  } else {
      $('.errorDetails').css({display: "none"});
  }
  $('.errorTitle').text(errorMessage);
  $('.errorBox').css({display: "block"});
}

function resetErrorBox() {
  $('.errorBox').css({display: "none"});

  $('.exceptionName').text('');
  $('.exceptionDescription').text('');
  $('.exceptionTraceback').text('');
}

function initializeCloseErrorBox() {
    $('.closeErrorBox').on('click', function() {
        $('.errorBox').css({display: "none"});
    });
}

function initializeButtonEvents() {
    var buttonIdToEndpoint = {
        '#curatedDatasetsButton': '/create_curated_datasets',  // Curated Datasets are created!
        '#kinesisButton': '/configure_kinesis',  // Kinesis applications created and streams are enabled!
        '#spectrumButton': '/run_spectrum_analytics',  // Successfully ran analytics with Spectrum!
        '#athenaRegisterButton': '/run_configure_athena',  // Successfully registered tables in Athena!
        '#glueCrawlButton': '/run_glue_crawler',  // AWS Glue schema discovery complete!
        '#quicksightPublishButton': '/publish_datasets' //  Successfully published datasets to Published Datasets S3 Bucket.
    };
    Object.keys(buttonIdToEndpoint).forEach(function(buttonId) {
        registerLoadingButton(buttonId, buttonIdToEndpoint[buttonId], 'Success!');
    });
    $('#elasticSearchButton').on('click', function() {
        $.post('/elastic_search', function(data) {
            updateState(data);
            changeNextButtonState();
            $('#elasticSearchButton').removeClass('btn-primary').addClass('btn-success');
        });
    });
    $('#amazonAthenaButton').on('click', function() {
        $.post('/amazon_athena', function(data) {
            updateState(data);
            changeNextButtonState();
            $('#amazonAthenaButton').removeClass('btn-primary').addClass('btn-success');
        });
    });
    $('#beginWalkthroughButton').on('click', function() { moveToStep(2); });
    $('#linkToPreviousStep').on('click', function(){ moveToStep(currentStep - 1); });
    $('#linkToNextStep').on('click', function(){ moveToStep(currentStep + 1);  });
    $('.step').on('click', function() {
        var step = parseInt(this.getAttribute('data-wizard-tab'));
        moveToStep(step);
    });
    $("#learnMoreForm").submit(function(event) {
        event.preventDefault();
        var form = $(this);
        var url = form.attr('action');
        var data = {
            name: $('#name').val(),
            role: $('#role').val(),
            email: $('#email').val(),
            company: $('#company').val(),
            message: $('#message').val()
        };
        $.post(url, data, function(data){
            updateState(data);
            showAlert('.learn-more-success');
        }).fail(function(xhr){
            updateErrorBox(xhr);
        });
    });
}

$(document).ready(function() {
    initializeButtonEvents();
    initializeCloseErrorBox();
    $.get('/step', function(data) {
        updateState(data);
        refreshNavigationSteps();
        activateTab();
        changeNextButtonState();
        changePrevButtonState();
    });
    $('[data-toggle="tooltip"]').tooltip({
        html: true,
        title: 'Encountered an issue? <a href="/faq">Visit FAQ</a>',
        delay: {
            show: 100,
            hide: 1200
        },
        placement: 'right'
    });
});
