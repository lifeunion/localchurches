/*
 *  jquery store locator 1.5
 *
 *  Made by altsniffer
 */
;( function( $, window, document, undefined ) {

	"use strict";

		// Create the defaults once
		var pluginName = "storeLocator",
			defaults = {
                remote: null,
                height: null,
                defaultLocation: null,
                mapOptions: {
                    zoom: 9,
                    minZoom: 4,
                    maxZoom: 16,
                    scrollwheel: true,
                    mapTypeId: google.maps.MapTypeId.ROADMAP,
                    mapTypeControl: true,
                    mapTypeControlOptions: {
                        style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
                        position: google.maps.ControlPosition.TOP_RIGHT
                    },
                    zoomControl: true,
                    zoomControlOptions: {
                        position: google.maps.ControlPosition.RIGHT_TOP
                    },
                    scaleControl: true,
                    streetViewControl: false,
                    streetViewControlOptions: {
                        position: google.maps.ControlPosition.RIGHT_BOTTOM
                    },
                    styles: [{
                        "featureType": "administrative",
                        "elementType": "labels.text.fill",
                        "stylers": [{"color": "#444444"}]
                    }, {
                        "featureType": "landscape",
                        "elementType": "all",
                        "stylers": [{"color": "#f2f2f2"}]
                    }, {
                        "featureType": "poi",
                        "elementType": "all",
                        "stylers": [{"visibility": "off"}]
                    }, {
                        "featureType": "road",
                        "elementType": "all",
                        "stylers": [{"saturation": -100}, {"lightness": 45}]
                    }, {
                        "featureType": "road.highway",
                        "elementType": "all",
                        "stylers": [{"visibility": "simplified"}]
                    }, {
                        "featureType": "road.arterial",
                        "elementType": "labels.icon",
                        "stylers": [{"visibility": "off"}]
                    }, {
                        "featureType": "transit",
                        "elementType": "all",
                        "stylers": [{"visibility": "off"}]
                    }, {
                        "featureType": "water",
                        "elementType": "all",
                        "stylers": [{"color": "#46bcec"}, {"visibility": "on"}]
                    }]
                },
                templates: {
                    list: 'mapListEntryTemplate',
                    detail: 'mapListDetailTemplate',
                },
                markerOptions: {
                    draggable: false,
                    bounceMarker: true,
                    markerIcon: BLA,
                    dropAnimation: false
                },
                categoriesOptions: {
                    categoryField: 'category',
                    showFilter: false,
                    filterPosition: google.maps.ControlPosition.LEFT_TOP,
                    template: null,
                    boundOnClick: false,
                    icons: null
                },
                detailsOptions: {
                    closeTrigger: '.map_details_close',
                    panorama: {
                        container: 'pano',
                        showPanorama: false,
                        notFoundText: 'Street View data not found for this location.',
                        searchRadius: 50
                    }
                },
                searchOptions: {
                    show: true,
                    placeholder: 'Enter your search term...',
                },
                listOptions: {
                    position: 'right',
                    sortByDistance: false,
                    distanceType: 'km', // or miles
                    updateOn: {
                        drag: true,
                        zoom: true,
                        resize: true
                    }
                },
                geoLocationOptions: {
                    show: true,
                    icon: BUL,
                    title: 'Show your Location',
                    zoom: 9,
                    position: google.maps.ControlPosition.TOP_LEFT,
                    index: 1
                },
                autocompleteOptions: {
                    show: true,
                    position: google.maps.ControlPosition.TOP_LEFT,
                    placeholder: 'find location by city',
                    country: 'all',
                    types: '(cities)',
                    zoom: 9,
                    class: 'map_btn_custom',
                    index: 2,
                    errorNotFound: 'No result for your search!'
                },
                markerCluster: {
                    cluster: true,
                    imagePath: 'https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m',
                    cssClass: 'custom-pin'
                },
                routeOptions: {
                    show: false,
                    headline: '<h3>Direction</h3>',
                    trigger: 'map_direction_trigger',
                    closeTrigger: 'map_direction_close_trigger',
                    closeHtml: 'close',
                    types: 'address',
                    country: null
                },
                notificationOptions: {
                    class: 'custom-class',
                    duration: 5000
                },
                responsiveOptions: [
                    {
                        breakpoint: 768,
                        settings: {
                            mapHeight: 400,
                            listHeight: 400
                        }
                    },
                    {
                        breakpoint: 480,
                        settings: {
                            mapHeight: 'full',
                            listHeight: 400
                        }
                    }
                ],
                onUpdateDetail: function() {},
                onUpdateList: function(){},
                onBeforeClickMarker: function() {}
			};

		// The actual plugin constructor
		function StoreLocator ( element, options ) {
			this.element = element;

			this.settings = $.extend( true, defaults, options );
			this._name = pluginName;
            this.markers = [];
            this._markers = {};
            this.stores = {};
            this._showData = [];
            this.itemCount;
            this._markerCluster = null;
            this._filterNavigationHeight = null;
            this._activeCategories = [];
            this.infowindow = null;
            this.zoomListener = null;
            this.init();
		}

		// Avoid Plugin.prototype conflicts
		$.extend( StoreLocator.prototype, {
            init: function () {
                if (this.settings.listOptions.position == 'right') {
                    $('.map_container').css('float', 'left');
                    $('.map_detail').addClass('from_right');
                } else if(this.settings.listOptions.position == 'left')
                {
                    $('.map_container').css('float', 'right');
                    $('.map_detail').addClass('from_left');
                }

                this._initMap();
                if(this.settings.remote == null) {
                    this._showNotification('No remote url specified.');
                    return;
                }

                var _ = this;
                $.ajax({
                    url: this.settings.remote,
                    async: false,
                    dataType: 'json',
                    success: $.proxy(function (data) {
                        this.stores = data;
                    }, this),
                    complete: $.proxy(function () {
                        this._initAfterDataLoaded();

                    }, this)
                });
            },
			_initAfterDataLoaded: function() {

                if (this.stores.length === 0) {
                    alert('no data found');
                }

                this._initResponsive();
                var _t = this;
                $(window).on('resize', function () {
                    _t._initResponsive();
                });

                this._initMarker();
                if(this.settings.defaultLocation == null)
                {
                    this._initList();
                }
                this._initClicks();

                if(this.settings.geoLocationOptions.show)
                {
                    if('https:' == document.location.protocol)
                    {
                        $('<div class="map_geotarget"><div class="map_btn_custom" title="' + this.settings.geoLocationOptions.title + '"><img src="' + this.settings.geoLocationOptions.icon + '" alt="' + this.settings.geoLocationOptions.title + '" /></div></div>');

                        var geoTargetContainer = document.createElement('div');
                        geoTargetContainer.style.margin = '10px';
                        geoTargetContainer.className = 'map_geotarget';

                        var controlUI = document.createElement('div');
                        controlUI.className = 'map_btn_custom';
                        geoTargetContainer.appendChild(controlUI);

                        var controlImage = document.createElement('img');
                        controlImage.src = this.settings.geoLocationOptions.icon;
                        controlImage.alt = this.settings.geoLocationOptions.title;
                        controlUI.appendChild(controlImage);

                        geoTargetContainer.index = this.settings.geoLocationOptions.index;
                        this.map.controls[this.settings.geoLocationOptions.position].push(geoTargetContainer);
                    } else {
                        this._showNotification('Only secure origins are allowed for GeoLocation. You need HTTPS.');
                    }
                }
                if(this.settings.autocompleteOptions.show)
                {
                    var autocompleteContainer = document.createElement('div');
                    autocompleteContainer.style.margin = '8px';

                    var autocompleteInput = document.createElement('input');
                    autocompleteInput.setAttribute('type', 'text');
                    autocompleteInput.setAttribute('class',this.settings.autocompleteOptions.class);
                    autocompleteInput.setAttribute('id', 'pac-input');
                    autocompleteInput.setAttribute('placeholder', this.settings.autocompleteOptions.placeholder);
                    autocompleteContainer.appendChild(autocompleteInput);

                    autocompleteContainer.index = this.settings.autocompleteOptions.index;
                    this.map.controls[this.settings.autocompleteOptions.position].push(autocompleteContainer);

                    var input = autocompleteInput;
                    var options = {
                        types: [this.settings.autocompleteOptions.types]
                    };

                    if (this.settings.autocompleteOptions.country !== null) {
                        if (this.settings.autocompleteOptions.country.toLowerCase() != 'all') {
                            options.componentRestrictions = {country: this.settings.autocompleteOptions.country}
                        }

                    }

                    var autocomplete = new google.maps.places.Autocomplete(input, options);

                    google.maps.event.addListener(autocomplete, 'place_changed', function () {
                        if(!this.getPlace().geometry)
                        {
                            _t._showNotification(_t.settings.autocompleteOptions.errorNotFound);
                            return false;
                        }
                        var latLng = new google.maps.LatLng(this.getPlace().geometry.location.lat(), this.getPlace().geometry.location.lng());
                        _t.map.setCenter(latLng);
                        _t.map.setZoom(_t.settings.autocompleteOptions.zoom);
                    });
                }

                if(this.settings.searchOptions.show)
                {
                    $('<div>', {
                        class: 'map_filter_box'
                    }).append($('<div>', {
                                class: 'map_filter_input'
                            }).append($('<input type="text">').attr('class', 'map_search_input')
                                    .attr('placeholder', this.settings.searchOptions.placeholder)
                                    .attr('name', 'search')
                                    .attr('id', 'search')
                            ).append($('<span>').attr('class', 'map_search_icon'))
                    ).appendTo('.map_listings_headline');
                }

                if(this.settings.categoriesOptions.showFilter)
                {
                    var filterContainer = document.createElement('div');
                    filterContainer.style.margin = '10px';
                    filterContainer.className = 'categories';
                    filterContainer.id = 'mapFilterNavigation';

                    if(this.settings.categoriesOptions.template)
                    {
                        filterContainer.innerHTML = this.settings.categoriesOptions.template;
                    }
                    else
                    {
                        if(this.settings.categoriesOptions.icons != null)
                        {
                            $.each(this.settings.categoriesOptions.icons, function (i) {

                                var navigationLink = document.createElement('a');
                                navigationLink.className = 'ucwords map-marker-filter-' + i;
                                navigationLink.setAttribute('data-cat', i)
                                navigationLink.innerHTML = i;
                                filterContainer.appendChild(navigationLink);
                            });
                            var navigationLink = document.createElement('a');
                            navigationLink.className = 'ucwords map-marker-filter-all';
                            navigationLink.setAttribute('data-cat', 'all')
                            navigationLink.innerHTML = 'show all';
                            filterContainer.appendChild(navigationLink);
                        }

                    }

                    filterContainer.index = this.settings.autocompleteOptions.index;
                    this.map.controls[this.settings.categoriesOptions.filterPosition].push(filterContainer);
                }

                if(this.settings.routeOptions.show)
                {
                    $('<div>', {
                        class: 'map_route',
                        id: 'map_route',
                    }).append(this.settings.routeOptions.headline)
                            .append($('<input type="text">').attr('class', 'map_direction_input')
                                    .attr('placeholder', this.settings.routeOptions.placeholder)
                                    .attr('name', 'origin')
                                    .attr('id', 'map_direction_input'))
                            .append($('<a>', {
                                class: 'map_direction_close_trigger',
                                html: this.settings.routeOptions.closeHtml
                            }))
                    .appendTo('.map_results');

                    this._directionsDisplay = new google.maps.DirectionsRenderer;
                    var directionsService = new google.maps.DirectionsService;

                    var triggerRoute = this._checkClassOrId(this.settings.routeOptions.trigger);
                    $(document).on('click', triggerRoute, function (e) {
                        if(!$('.map_route').hasClass('open'))
                        {
                            $('.map_route').addClass('open');
                            e.preventDefault();

                            var origin = '';

                            if($('.map_direction_input').val().length > 0)
                            {
                                origin = $('.map_direction_input').val();
                            }

                            var templateItem = $(this).tmplItem();
                            if($.isEmptyObject(templateItem.data) === false)
                            {
                                var destination = templateItem.data.location.latitude + ',' + templateItem.data.location.longitude;
                                _t._routeDestination = destination;
                                if(origin.length > 0)
                                {
                                    _t._directionsDisplay.setMap(_t.map);
                                    _t._directionsDisplay.setPanel(document.getElementById('map_route'));

                                    _t._calculateAndDisplayRoute(directionsService, _t._directionsDisplay, origin, destination);
                                }
                            }
                        }

                    });

                    var closeTriggerRoute = this._checkClassOrId(this.settings.routeOptions.closeTrigger);
                    $(document).on('click', closeTriggerRoute, $.proxy(_t._closeDirections, _t));

                    var input = document.getElementById('map_direction_input');
                    var options = {
                        types: [this.settings.routeOptions.types],
                        componentRestrictions: {country: this.settings.routeOptions.country}
                    };
                    if(this.settings.routeOptions.country != null)
                    {
                        var options = {
                            types: [this.settings.routeOptions.types],
                            componentRestrictions: {country: this.settings.routeOptions.country}
                        };
                    }
                     else {
                        var options = {
                            types: [this.settings.routeOptions.types],
                        };
                    }
                    var autocomplete = new google.maps.places.Autocomplete(input, options);

                    google.maps.event.addListener(autocomplete, 'place_changed', function () {
                        if(!this.getPlace())
                        {
                            return;
                        }
                        var latLng = new google.maps.LatLng(this.getPlace().geometry.location.lat(), this.getPlace().geometry.location.lng());
                        var origin = latLng;
                        if(_t._routeDestination)
                        {
                            _t._directionsDisplay.setMap(_t.map);
                            _t._directionsDisplay.setPanel(document.getElementById('map_route'));

                            var destination = _t._routeDestination;
                            _t._calculateAndDisplayRoute(directionsService, _t._directionsDisplay, origin, destination);
                        }
                    });
                }
                $(document).on('mouseenter', '.result_item', function() {
                    var hoverId = $(this).data('id');
                    _t._markers[hoverId].setAnimation(google.maps.Animation.BOUNCE);
                     setTimeout(function(){ _t._markers[hoverId].setAnimation(null); }, 750);
                });
                $(document).on('mouseleave', '.result_item', function() {
                    var hoverId = $(this).data('id');
                    _t._markers[hoverId].setAnimation(null);
                });

                google.maps.event.addListenerOnce(this.map, 'tilesloaded', $.proxy(function() {

                    if (this.settings.listOptions.updateOn.zoom) {
                        _t.zoomListener = google.maps.event.addListener(this.map, 'zoom_changed', $.proxy(this._getInViewportMarkers, this));
                    }

                    if (this.settings.listOptions.updateOn.drag) {
                       google.maps.event.addListener(this.map, 'dragend', $.proxy(this._getInViewportMarkers, this));
                    }

                    if(this.settings.listOptions.updateOn.resize) {
                        google.maps.event.addListener(this.map, 'resize', $.proxy(this._getInViewportMarkers, this));
                        google.maps.event.addDomListener(window, "resize",$.proxy(function() {
                            if(this.settings.defaultLocation == null)
                            {
                                this.map.fitBounds(this._bounds);
                            }
                        }, this));

                    }
                }, this));
			},
			_initMap: function( ) {
                this.map = new google.maps.Map( $(this.element)[0],this.settings.mapOptions);
			},
            _initMarker: function( ) {
                this._createMarkers();
                if (this.settings.defaultLocation != null) {
                    this._initDefaultLocation();
                }
                else
                {
                    if(this.settings.listOptions.sortByDistance)
                    {
                        this.map.setCenter(this._bounds.getCenter());
                    }
                    this.map.fitBounds(this._bounds);
                }
            },
            _initDefaultLocation: function () {

                var defaultLocation = this.settings.defaultLocation, latLng;
                var countMarkers = 0;

                if (defaultLocation instanceof Array) {
                    latLng = new google.maps.LatLng(defaultLocation[0], defaultLocation[1]);
                }
                
                this.map.setCenter(latLng);
                this.settings.geoLocationOptions.zoom = 16;
                this.map.setZoom(this.settings.geoLocationOptions.zoom);

                if (countMarkers < 3) {
                    for(var i = 0; i < this.markers.length; i++) {
                            if (this.map.getBounds().contains(this.markers[i].position))
                            {
                                countMarkers = countMarkers+1;
                            }
                    }
                    this.settings.geoLocationOptions.zoom = 14;
                    this.map.setZoom(this.settings.geoLocationOptions.zoom);
                }

                if (countMarkers < 3) {
                    for(var i = 0; i < this.markers.length; i++) {
                            if (this.map.getBounds().contains(this.markers[i].position))
                            {
                                countMarkers = countMarkers+1;
                            }
                    }
                    this.settings.geoLocationOptions.zoom = 12;
                    this.map.setZoom(this.settings.geoLocationOptions.zoom);
                }

                if (countMarkers < 3) {
                    for(var i = 0; i < this.markers.length; i++) {
                            if (this.map.getBounds().contains(this.markers[i].position))
                            {
                                countMarkers = countMarkers+1;
                            }
                    }
                    this.settings.geoLocationOptions.zoom = 10;
                    this.map.setZoom(this.settings.geoLocationOptions.zoom);
                }

                if (countMarkers < 3) {
                    for(var i = 0; i < this.markers.length; i++) {
                            if (this.map.getBounds().contains(this.markers[i].position))
                            {
                                countMarkers = countMarkers+1;
                            }
                    }
                    this.settings.geoLocationOptions.zoom = 8;
                    this.map.setZoom(this.settings.geoLocationOptions.zoom);
                }


                var _t = this;
                this._boundInitListener = google.maps.event.addListener(_t.map, 'bounds_changed', function () {
                    _t._getInViewportMarkers();
                });

            },
            _initClicks: function () {
                var _ = this;
                $(document).on('click', '.result_item a', function(e) {
                    e.preventDefault();
                    var templateItem = $(this).tmplItem();
                    if($.isEmptyObject(templateItem.data) === false)
                    {
                        _._updateDetail(templateItem.data);
                    }
                });

                $(document).on('click', '.filter_minimize', function () {

                    var filterNavigation = $('#mapFilterNavigation');
                    if(_._filterNavigationHeight == null)
                    {
                        _._filterNavigationHeight = filterNavigation.innerHeight();
                    }
                    filterNavigation.height(_._filterNavigationHeight);
                    if (filterNavigation.hasClass('minimized')) {
                        filterNavigation.removeClass('minimized');
                    }
                    else {
                        var headlineHeight = $(this).outerHeight(true);
                        filterNavigation.height(headlineHeight);
                        filterNavigation.addClass('minimized');
                    }
                });

                $(document).on('click', '.map_geotarget', function() {
                    var that = _;
                    if (navigator.geolocation) {
                      navigator.geolocation.getCurrentPosition($.proxy(_._geolocationSuccess, _), _._geolocationError);
                    } else {
                        that._showNotification('geolocation not supported.');
                    }
                });

                $(document).on('click', '.map_search_icon', function () {
                    var filterInput = $('.map_filter_input');
                    if(filterInput.hasClass('input_open'))
                    {
                        filterInput.removeClass('input_open');
                    } else {
                        filterInput.addClass('input_open');
                    }
                });

                $(document).on('keyup', '#search', function () {
                    var filter = $(this).val(), count = 0;
                    $(".result_item").each(function () {
                        if ($(this).text().search(new RegExp(filter, "i")) < 0) {
                            $(this).fadeOut();
                        } else {
                            $(this).show();
                            count++;
                        }
                    });
                });

                $(document).on('click', '.categories a', function(e) {
                    e.preventDefault();

                    if ($(this).hasClass('map-marker-filter-all')) {
                        $('.categories a').not(this).removeClass('active');
                        $(this).addClass('active');
                        _._activeCategories = [];
                    } else {
                        var cat = $(this).data('cat');

                        if ($(this).hasClass('active')) {
                            _._activeCategories = $.grep(_._activeCategories, function(value) {
                              return value != cat;
                            });
                            $(this).removeClass('active');
                        } else {
                            $(this).addClass('active');
                            _._activeCategories.push(cat);
                        }
                    }

                    _._createMarkers();
                    if(_.settings.categoriesOptions.boundOnClick)
                    {
                        if (_.settings.listOptions.updateOn.zoom) {
                            if (_.zoomListener) {
                                google.maps.event.removeListener(_.zoomListener);
                            }
                        }
                        _.map.fitBounds(_._bounds);
                        _._initList();
                        if (_.settings.listOptions.updateOn.zoom) {
                            _.zoomListener = google.maps.event.addListener(_.map, 'zoom_changed', $.proxy(_._getInViewportMarkers, _));
                        }
                    } else {
                        _._getInViewportMarkers();
                    }

                });

                $(document).on('click', this.settings.detailsOptions.closeTrigger, function(e) {
                    e.preventDefault();
                   _.closeDetail();
                });

            },
            _geolocationSuccess: function (position) {
                var latLng = new google.maps.LatLng(position.coords.latitude, position.coords.longitude);
                this.map.setCenter(latLng);
                this.map.setZoom(this.settings.geoLocationOptions.zoom);
            },
            _geolocationError: function (msg) {
                 this._showNotification(msg)
            },
            _checkClassOrId: function (name) {
                var t = name;
                if(document.getElementsByClassName(name).length != 0){
                    t = '.' + name;
                }
                else if (document.getElementById(name) != null){
                    t = '#' + name;
                } else {
                    t = '.' + name;
                }

                return t;
            },
            _createMarkers: function () {
                this._removeMarkers();

                var bounds = new google.maps.LatLngBounds();
                var itemCount = 0;

                this.markers = [];
                this._showData = [];

                var filter = this._activeCategories;

                for (var x = 0; x < this.stores.length; x++) {

                    var data = this.stores[x];

                    var categoryField = this.settings.categoriesOptions.categoryField;
                    var markerIcon;
                    var categoryName = data[categoryField];

                    if ($.isEmptyObject(filter) === false) {
                        if ($.inArray(categoryName, filter) === -1) {
                            continue;
                        }
                    }

                    this._showData.push(data);

                    if (this.settings.categoriesOptions.icons != null && this.settings.categoriesOptions.icons[categoryName]) {
                        markerIcon = this.settings.categoriesOptions.icons[categoryName];
                    }
                    else {
                        markerIcon = this.settings.markerOptions.markerIcon;
                    }
                    var latLng = new google.maps.LatLng(data.location.latitude, data.location.longitude);

                    var marker = new google.maps.Marker({
                        position: latLng,
                        map: this.map,
                        icon: markerIcon,
                        draggable: this.settings.markerOptions.draggable,
                        itemId: data.id,
                    });

                    this.infowindow = new google.maps.InfoWindow();
                    var _map = this.map;
                    var trimmed_address = encodeURIComponent(data.meeting_address.trim());
                    var content = '<b>' + '<h6>'+ 'Church in ' + data.locality_name + '</h6></b>' + data.meeting_address + '<br>'
                    + '<a class="label label-success label-map" href='+
                    'https://www.localchurches.org'+ data.url + '>'+ 'more info' + '</a>' +
                    '<a class="label label-danger label-map" href=' + 
                    'https://maps.google.com/?saddr=Current%20Location&daddr='+ trimmed_address + '>'+ 'get directions here' + '</a>';

                    var _ = this;

                    google.maps.event.addListener(marker,'click', (function (marker, content) {
                        return function () {
                            if (_.infowindow) {
                                _.infowindow.close();
                            }
                            _.infowindow.setContent(content);
                            _.infowindow.open(_map,marker);
                        };
                     })(marker, content));

                    /*google.maps.event.addListener(marker,'click', (function(marker,content,infowindow, _map){
                        return function() {
                            if (this.infowindow) {
                                this.infowindow.close();
                            }
                            this.infowindow.setContent(marker.content);
                            this.infowindow.open(_map,marker);
                        };
                     })(marker,content,infoWindow));
                    */

                    if(this.settings.markerOptions.dropAnimation)
                    {
                        marker.setAnimation(google.maps.Animation.DROP);
                    }

                    this._markers[data.id] = marker;
                    this.markers.push(marker);

                    var _ = this;

                    google.maps.event.addListener(marker, 'click', this._handleMarkerClick.bind(undefined, marker, data, this));
                    google.maps.event.addListener(marker, 'mouseover', this._handleMarkerMouseover.bind(undefined, marker, data, this));

                    google.maps.event.addListener(marker, 'mouseout', function() {
                        $('.map_listings_results .result_item').removeClass('active');
                    });

                    bounds.extend(latLng);
                    ++itemCount;
                }
                this._bounds = bounds;

                this.itemCount = itemCount;
                if (this.settings.markerCluster.cluster) {
                    this._markerCluster = new MarkerClusterer(this.map, this.markers,
                        {
                            imagePath: this.settings.markerCluster.imagePath,
                            cssClass: this.settings.markerCluster.cssClass

                        });
                }
            },
            _handleMarkerClick: function (marker, data, that) {
                var callback = that.settings.onBeforeClickMarker;
                if ($.isFunction(callback)) {
                    callback.call(this, data);
                }
                that._updateDetail(data);
                if(that.settings.routeOptions.show)
                {
                    that._closeDirections();
                }

            },
            _handleMarkerMouseover: function (marker, data, that) {
                var item = $('*[data-id="'+ data.id +'"]');

                item.addClass('active');
            },
            _getInViewportMarkers: function () {
                this.viewPortMarkers = [];
                for(var i = 0; i < this.markers.length; i++)
                {
                    if (this.map.getBounds().contains(this.markers[i].position))
                    {
                        this.viewPortMarkers[i] = this.markers[i].itemId;
                    }
                }
                google.maps.event.removeListener(this._boundInitListener);
                this._updateList();
            },
            _removeMarkers: function () {
                for(var i = 0; i < this.markers.length; i++)
                {
                    this.markers[i].setMap(null);
                }
                if (this.settings.markerCluster.cluster) {
                    if(this._markerCluster)
                    {
                        this._markerCluster.clearMarkers();
                    }
                }
            },
            _initList: function () {

                if (this.settings.listOptions.sortByDistance)
                {
                    var centerLatLng = new google.maps.LatLng(this.map.getCenter().lat(), this.map.getCenter().lng());

                    for (var k = 0; k < this._showData.length; k++)
                    {
                        var LatLng = new google.maps.LatLng(this._showData[k].location.latitude, this._showData[k].location.longitude);
                        var distance = google.maps.geometry.spherical.computeDistanceBetween(centerLatLng, LatLng);

                        if (this.settings.listOptions.distanceType == 'miles') {
                            distance = distance * 0.000621371192;
                        } else {
                            distance = distance / 1000;
                        }
                        this._showData[k].distance = distance.toFixed(1);
                    }
                    this._showData.sort(this._sortByDistance);
                }

                $(".map_listings_results").html('');
                $("#" + this.settings.templates.list).tmpl(this._showData).appendTo(".map_listings_results");
                this._updateCount();
                var callback = this.settings.onUpdateList;
                if ($.isFunction(callback)) {

                    callback.call(this);
                }
            },
            _updateList: function () {

                var data = this._showData;
                var listItems = [];

                if(this.settings.listOptions.sortByDistance)
                {
                    var centerLatLng = new google.maps.LatLng(this.map.getCenter().lat(), this.map.getCenter().lng());
                }
                for(var i = 0; i < this.viewPortMarkers.length; i++)
                {
                    for(var k = 0; k < data.length; k++)
                    {
                       if(this.viewPortMarkers[i] == data[k].id)
                       {
                           if(this.settings.listOptions.sortByDistance)
                           {
                               var LatLng = new google.maps.LatLng(data[k].location.latitude, data[k].location.longitude);
                               var distance = google.maps.geometry.spherical.computeDistanceBetween(centerLatLng, LatLng);

                               if (this.settings.listOptions.distanceType == 'miles') {
                                   distance = distance * 0.000621371192;
                               } else {
                                   distance = distance / 1000;
                               }
                               data[k].distance = distance.toFixed(1);
                           }

                           listItems.push(data[k]);
                       }
                    }
                }
                if(this.settings.listOptions.sortByDistance)
                {
                    listItems.sort(this._sortByDistance);
                }

                this.itemCount = listItems.length;
                this._updateCount();
                $(".map_listings_results").html('');
                $("#" + this.settings.templates.list).tmpl(listItems).appendTo(".map_listings_results");

                var callback = this.settings.onUpdateList;
                if ($.isFunction(callback)) {

                    callback.call(this, data);
                }
            },
            _sortByDistance: function(a,b) {
               return (a.distance - b.distance)
            },
            _updateDetail: function(data) {

                $(".map_detail").html('');
                $("#" + this.settings.templates.detail).tmpl(data).appendTo(".map_detail");
                $(".map_results").addClass("detail_open");
                if(this.settings.detailsOptions.panorama.showPanorama)
                {
                    var sv = new google.maps.StreetViewService();
                    var fenway = new google.maps.LatLng(data.location.latitude, data.location.longitude);
                    var panoramaSetting = this.settings.detailsOptions.panorama;

                    sv.getPanorama({location: fenway, radius: this.settings.detailsOptions.panorama.searchRadius}, function (data, status) {
                        if (status === google.maps.StreetViewStatus.OK) {
                            var panorama = new google.maps.StreetViewPanorama(document.getElementById(panoramaSetting.container));
                            panorama.setPano(data.location.pano);
                            panorama.setPov({
                                heading: 270,
                                pitch: 0
                            });
                            panorama.setVisible(true);
                        } else {
                            $('#' + panoramaSetting.container).css({
                                'background-color': 'transparent',
                                'height': 'auto',
                                'width': '100%'
                            });
                            $('#' + panoramaSetting.container).html(panoramaSetting.notFoundText);
                        }
                    });
                }
                var callback = this.settings.onUpdateDetail;
                if ($.isFunction(callback)) {
                    callback.call(this, data);
                }
            },
            _updateCount: function () {
                $('.map_listings_headline .map_listings_number').html('('+this.itemCount+')');
            },
            closeDetail: function () {
                $(".map_results").removeClass("detail_open");
                setTimeout(function () {
                    $(".map_detail").html("");
                }, 700);
            },
            _calculateAndDisplayRoute: function(directionsService, directionsDisplay, start, end) {
                var that = this;

                directionsService.route({
                    origin: start,
                    destination: end,
                    travelMode: google.maps.TravelMode.DRIVING
                }, function (response, status) {
                    if (status === google.maps.DirectionsStatus.OK) {
                        directionsDisplay.setDirections(response);
                    } else {
                        that._showNotification('Directions request failed due to ' + status);
                    }
                });

            },
            _closeDirections: function () {

                if ($('.map_route').hasClass('open'))
                {
                    $('.map_route').removeClass('open');
                    this._directionsDisplay.setMap(null);
                }
            },
            _showNotification: function (message) {
                $('<div>', {
                    id: 'map_notification',
                    class: this.settings.notificationOptions.class,

                }).append(message).appendTo('.map_container').fadeIn('slow');

                setTimeout(function() {
                    $('#map_notification').fadeOut('slow',function() { $('#map_notification').remove(); });
                }, this.settings.notificationOptions.duration);
            },
            _initResponsive: function () {
                var w = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
                var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);

                var _ = this, targetBreakpoint, settings;
                var respondToWidth = window.innerWidth || $(window).width();


                for (var i = 0, l = _.settings.responsiveOptions.length; i < l; i++) {
                    if (respondToWidth <= _.settings.responsiveOptions[i].breakpoint) {
                        targetBreakpoint = _.settings.responsiveOptions[i].breakpoint;
                    }
                }

                $(_.settings.responsiveOptions).each(function (key, val) {
                    if (targetBreakpoint == val.breakpoint) {
                        settings = val.settings;
                    }
                });

                var mapHeight = h;
                var listHeight;

                var mapWrapper = $('.map_wrapper');

                if(typeof settings === 'undefined')
                {
                    if(this.settings.height != null && this.settings.height.length > 0)
                    {
                        mapWrapper.height(this.settings.height);
                    } else
                    {
                        mapWrapper.css('height', h);
                    }

                    $('.map_container').css('height', '100%');
                    $('.map_results').css('height', '100%');
                }
                else {
                    mapWrapper.css('height', 'auto');
                    if (settings.mapHeight === 'full') {
                        mapHeight = h;
                    } else {
                        mapHeight = settings.mapHeight;
                    }

                    listHeight = settings.listHeight;

                    $('.map_container').css('height', mapHeight);
                    $('.map_results').css('height', listHeight);
                }

                if (this.settings.categoriesOptions.showFilter) {
                    setTimeout(function () {
                        var element = $('#mapFilterNavigation');

                        if (element.length > 0) {
                            var mapContainerHeight = $(".map_container").height();
                            var elHeight = $(element).outerHeight(true);
                            var elOffset = $(element).position().top;

                            if (mapContainerHeight - (elHeight + elOffset) < 0) {
                                $(element).css('height', mapContainerHeight - (elOffset + 50));
                                $(element).css('overflow', 'auto');
                            } else {
                                $(element).css('overflow', 'hidden');
                                $(element).css('height', 'auto');
                            }
                        }
                    }, 1000);
                }
            }
		});

		// A really lightweight plugin wrapper around the constructor,
		// preventing against multiple instantiations
		$.fn[ pluginName ] = function( options ) {
			return this.each( function() {
				if ( !$.data( this, "plugin_" + pluginName ) ) {
					$.data( this, "plugin_" +
						pluginName, new StoreLocator( this, options ) );
				}
			} );
		};

} )( jQuery, window, document );