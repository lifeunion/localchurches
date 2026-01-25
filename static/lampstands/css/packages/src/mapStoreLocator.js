/**
 * mapStoreLocator – vanilla JS map/store locator (Alpine.js–friendly)
 * Refactored from jquery store locator; no jQuery. List/detail driven via Alpine.store('mapStore').
 */
(function (window, document) {
	"use strict";

	function deepMerge(target, source) {
		var k;
		for (k in source) {
			if (source.hasOwnProperty(k)) {
				if (source[k] && typeof source[k] === "object" && !Array.isArray(source[k]) && !(source[k] instanceof google.maps.LatLng) && !(source[k] instanceof google.maps.LatLngBounds)) {
					if (!target[k] || typeof target[k] !== "object") target[k] = {};
					deepMerge(target[k], source[k]);
				} else {
					target[k] = source[k];
				}
			}
		}
		return target;
	}

	function getDefaults() {
		return {
			remote: null,
			height: null,
			defaultLocation: null,
			viewport: null,
			mapOptions: {
				zoom: 9,
				minZoom: 4,
				maxZoom: 16,
				scrollwheel: true,
				mapTypeId: google.maps.MapTypeId.ROADMAP,
				mapTypeControl: true,
				mapTypeControlOptions: { style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR, position: google.maps.ControlPosition.TOP_RIGHT },
				zoomControl: true,
				zoomControlOptions: { position: google.maps.ControlPosition.RIGHT_TOP },
				scaleControl: true,
				streetViewControl: false,
				streetViewControlOptions: { position: google.maps.ControlPosition.RIGHT_BOTTOM },
				styles: [
					{ featureType: "administrative", elementType: "labels.text.fill", stylers: [{ color: "#444444" }] },
					{ featureType: "landscape", elementType: "all", stylers: [{ color: "#f2f2f2" }] },
					{ featureType: "poi", elementType: "all", stylers: [{ visibility: "off" }] },
					{ featureType: "road", elementType: "all", stylers: [{ saturation: -100 }, { lightness: 45 }] },
					{ featureType: "road.highway", elementType: "all", stylers: [{ visibility: "simplified" }] },
					{ featureType: "road.arterial", elementType: "labels.icon", stylers: [{ visibility: "off" }] },
					{ featureType: "transit", elementType: "all", stylers: [{ visibility: "off" }] },
					{ featureType: "water", elementType: "all", stylers: [{ color: "#46bcec" }, { visibility: "on" }] }
				]
			},
			templates: { list: "mapListEntryTemplate", detail: "mapListDetailTemplate" },
			markerOptions: { draggable: false, bounceMarker: true, markerIcon: typeof BLA !== "undefined" ? BLA : "", dropAnimation: false },
			categoriesOptions: { categoryField: "category", showFilter: false, filterPosition: google.maps.ControlPosition.LEFT_TOP, template: null, boundOnClick: false, icons: null },
			detailsOptions: { closeTrigger: ".map_details_close", panorama: { container: "pano", showPanorama: false, notFoundText: "Street View data not found for this location.", searchRadius: 50 } },
			searchOptions: { show: true, placeholder: "Enter your search term..." },
			listOptions: { position: "right", sortByDistance: false, distanceType: "km", updateOn: { drag: true, zoom: true, resize: true } },
			geoLocationOptions: { show: true, icon: typeof BUL !== "undefined" ? BUL : "", title: "Show your Location", zoom: 9, position: google.maps.ControlPosition.TOP_LEFT, index: 1 },
			autocompleteOptions: { show: true, position: google.maps.ControlPosition.TOP_LEFT, placeholder: "find location by city", country: "all", types: "(cities)", zoom: 9, class: "map_btn_custom", index: 2, errorNotFound: "No result for your search!" },
			markerCluster: { cluster: true, imagePath: "https://developers.google.com/maps/documentation/javascript/examples/markerclusterer/m", cssClass: "custom-pin" },
			routeOptions: { show: false, headline: "<h3>Direction</h3>", trigger: "map_direction_trigger", closeTrigger: "map_direction_close_trigger", closeHtml: "close", types: "address", country: null },
			notificationOptions: { class: "custom-class", duration: 5000 },
			responsiveOptions: [ { breakpoint: 768, settings: { mapHeight: 400, listHeight: 400 } }, { breakpoint: 480, settings: { mapHeight: "full", listHeight: 400 } } ],
			onUpdateDetail: function () {},
			onUpdateList: function () {},
			onBeforeClickMarker: function () {}
		};
	}

	function MapStoreLocator(element, options) {
		this.element = element && (element.nodeType ? element : element[0]) ? (element.nodeType ? element : element[0]) : element;
		this.settings = deepMerge(getDefaults(), options || {});
		this.markers = [];
		this._markers = {};
		this.stores = [];
		this._showData = [];
		this.itemCount = 0;
		this._markerCluster = null;
		this._filterNavigationHeight = null;
		this._activeCategories = [];
		this.infowindow = null;
		this.zoomListener = null;
		this._routeOrigin = null;
		this._routeDestination = null;
		this._directionsDisplay = null;
		this._dirSvc = null;
		this._boundInitListener = null;
		this.init();
	}

	function qs(sel, root) { return (root || document).querySelector(sel); }
	function qsAll(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
	function on(el, ev, fn) { if (el) el.addEventListener(ev, fn); }

	MapStoreLocator.prototype._getStore = function () {
		return window.Alpine && window.Alpine.store && window.Alpine.store("mapStore");
	};

	MapStoreLocator.prototype._pushList = function (items) {
		var s = this._getStore();
		var n = (items || []).length;
		this.itemCount = n;
		if (s) { s.listItems = items || []; s.itemCount = n; }
		this._updateCount();
	};

	MapStoreLocator.prototype._pushDetail = function (data) {
		var s = this._getStore();
		if (s) s.detail = data;
		var mr = qs(".map_results");
		if (mr) mr.classList.add("detail_open");
	};

	MapStoreLocator.prototype._pushCount = function (n) {
		this.itemCount = n;
		this._updateCount();
	};

	MapStoreLocator.prototype._updateCount = function () {
		var s = this._getStore();
		if (s) s.itemCount = this.itemCount;
		// When using Alpine, the count is rendered via x-text; skip DOM write.
		if (!s) {
			var el = qs(".map_listings_headline .map_listings_number");
			if (el) el.textContent = "(" + this.itemCount + ")";
		}
	};

	MapStoreLocator.prototype._clearDetail = function () {
		var s = this._getStore();
		if (s) s.detail = null;
		var mr = qs(".map_results");
		if (mr) mr.classList.remove("detail_open");
		// When using Alpine, detail is rendered by x-if; do not clear innerHTML.
		if (!s) {
			setTimeout(function () {
				var d = qs(".map_detail");
				if (d) d.innerHTML = "";
			}, 700);
		}
	};

	MapStoreLocator.prototype._findById = function (id) {
		for (var i = 0; i < this._showData.length; i++) if (String(this._showData[i].id) === String(id)) return this._showData[i];
		return null;
	};

	MapStoreLocator.prototype.init = function () {
		var c = qs(".map_container"), d = qs(".map_detail");
		if (this.settings.listOptions.position === "right") {
			if (c) c.style.float = "left";
			if (d) d.classList.add("from_right");
		} else if (this.settings.listOptions.position === "left") {
			if (c) c.style.float = "right";
			if (d) d.classList.add("from_left");
		}
		this._initMap();
		if (!this.settings.remote) {
			this._showNotification("No remote url specified.");
			return;
		}
		var self = this;
		fetch(this.settings.remote)
			.then(function (r) { return r.json(); })
			.then(function (data) {
				self.stores = Array.isArray(data) ? data : [];
				self._initAfterDataLoaded();
			})
			.catch(function () { self._initAfterDataLoaded(); });
	};

	MapStoreLocator.prototype._initMap = function () {
		this.map = new google.maps.Map(this.element, this.settings.mapOptions);
	};

	MapStoreLocator.prototype._initAfterDataLoaded = function () {
		if (this.stores.length === 0) alert("no data found");
		var _t = this;
		this._initResponsive();
		on(window, "resize", function () { _t._initResponsive(); });
		this._initMarker();
		if (this.settings.defaultLocation == null) this._initList();
		this._initClicks();

		// Geo
		if (this.settings.geoLocationOptions.show && document.location.protocol === "https:") {
			var g = document.createElement("div");
			g.style.margin = "10px";
			g.className = "map_geotarget";
			var ui = document.createElement("div");
			ui.className = "map_btn_custom";
			ui.title = this.settings.geoLocationOptions.title;
			var img = document.createElement("img");
			img.src = this.settings.geoLocationOptions.icon;
			img.alt = this.settings.geoLocationOptions.title;
			ui.appendChild(img);
			g.appendChild(ui);
			g.style.cursor = "pointer";
			on(g, "click", function () {
				if (navigator.geolocation) navigator.geolocation.getCurrentPosition(_t._geolocationSuccess.bind(_t), _t._geolocationError.bind(_t));
				else _t._showNotification("geolocation not supported.");
			});
			this.map.controls[this.settings.geoLocationOptions.position].push(g);
		} else if (this.settings.geoLocationOptions.show) {
			this._showNotification("Only secure origins are allowed for GeoLocation. You need HTTPS.");
		}

		// Autocomplete (Place Autocomplete Element)
		if (this.settings.autocompleteOptions.show) {
			var ac = document.createElement("div");
			ac.style.margin = "8px";
			ac.style.width = "33%";
			ac.style.overflow = "visible";
			var _t = this;
			(function go() {
				if (typeof google.maps === "undefined" || typeof google.maps.importLibrary !== "function") {
					ac.innerHTML = "Autocomplete unavailable.";
					ac.index = _t.settings.autocompleteOptions.index;
					_t.map.controls[_t.settings.autocompleteOptions.position].push(ac);
					return;
				}
				google.maps.importLibrary("places").then(function (lib) {
					var P = lib.PlaceAutocompleteElement || (lib.place && lib.place.PlaceAutocompleteElement);
					if (!P) {
						ac.innerHTML = "Autocomplete unavailable.";
						ac.index = _t.settings.autocompleteOptions.index;
						_t.map.controls[_t.settings.autocompleteOptions.position].push(ac);
						return;
					}
					var o = { placeholder: _t.settings.autocompleteOptions.placeholder || "Type and select city name here" };
					if (_t.settings.autocompleteOptions.types && _t.settings.autocompleteOptions.types !== "all")
						o.includedPrimaryTypes = ["locality", "administrative_area_level_1", "administrative_area_level_2"];
					if (_t.settings.autocompleteOptions.country && _t.settings.autocompleteOptions.country.toLowerCase() !== "all")
						o.includedRegionCodes = _t.settings.autocompleteOptions.country.toLowerCase().split(/[,\s]+/).filter(Boolean);
					var pe = new P(o);
					pe.id = "pac-input";
					pe.className = _t.settings.autocompleteOptions.class || "";
					ac.appendChild(pe);
					on(pe, "gmp-select", function (ev) {
						var pp = ev.placePrediction;
						if (!pp || typeof pp.toPlace !== "function") return;
						var place = pp.toPlace();
						place.fetchFields({ fields: ["location", "viewport"] }).then(function () {
							if (!place.location) { _t._showNotification(_t.settings.autocompleteOptions.errorNotFound || "Place not found"); return; }
							var loc = place.location;
							var lat = typeof loc.lat === "function" ? loc.lat() : loc.lat;
							var lng = typeof loc.lng === "function" ? loc.lng() : loc.lng;
							var latLng = new google.maps.LatLng(lat, lng);
							if (place.viewport) {
								var v = place.viewport;
								var sw = (v.getSouthWest && v.getSouthWest()) || { lat: function () { return v.south; }, lng: function () { return v.west; } };
								var ne = (v.getNorthEast && v.getNorthEast()) || { lat: function () { return v.north; }, lng: function () { return v.east; } };
								var c = (typeof sw.lat === "function" ? sw.lat() : sw.lat) + "," + (typeof sw.lng === "function" ? sw.lng() : sw.lng) + "," + (typeof ne.lat === "function" ? ne.lat() : ne.lat) + "," + (typeof ne.lng === "function" ? ne.lng() : ne.lng);
								var mc = qs(".map_container");
								var dim = { height: mc ? mc.getBoundingClientRect().height : 400, width: mc ? mc.getBoundingClientRect().width : 600 };
								_t.settings.autocompleteOptions.zoom = _t._getBoundsZoomLevel(c, dim) - 1;
							}
							_t.map.setCenter(latLng);
							_t.map.setZoom(_t.settings.autocompleteOptions.zoom);
						}).catch(function () { _t._showNotification(_t.settings.autocompleteOptions.errorNotFound || "Place not found"); });
					});
					on(pe, "keydown", function (ev) {
						if ((ev.key !== "Enter" && ev.key !== "Return") || ev.defaultPrevented) return;
						var r = pe.shadowRoot;
						if (!r) return;
						var t = r.querySelector("[part=prediction-item-selected]") || r.querySelector("[part=prediction-item]");
						if (t) { t.click(); ev.preventDefault(); }
					});
					ac.index = _t.settings.autocompleteOptions.index;
					_t.map.controls[_t.settings.autocompleteOptions.position].push(ac);
					var p = ac.parentElement;
					if (p) { p.style.overflow = "visible"; p = p.parentElement; }
					if (p) p.style.overflow = "visible";
				}).catch(function () {
					ac.innerHTML = "Autocomplete could not be loaded.";
					ac.index = _t.settings.autocompleteOptions.index;
					_t.map.controls[_t.settings.autocompleteOptions.position].push(ac);
				});
			})();
		}

		// Search box
		if (this.settings.searchOptions.show) {
			var h = qs(".map_listings_headline");
			if (h) {
				var box = document.createElement("div");
				box.className = "map_filter_box";
				var inp = document.createElement("div");
				inp.className = "map_filter_input";
				var i = document.createElement("input");
				i.type = "text";
				i.className = "map_search_input";
				i.placeholder = this.settings.searchOptions.placeholder;
				i.name = "search";
				i.id = "search";
				var sp = document.createElement("span");
				sp.className = "map_search_icon";
				inp.appendChild(i);
				inp.appendChild(sp);
				box.appendChild(inp);
				h.appendChild(box);
			}
		}

		// Route
		if (this.settings.routeOptions.show) {
			var mrd = document.createElement("div");
			mrd.className = "map_route";
			mrd.id = "map_route";
			mrd.innerHTML = (this.settings.routeOptions.headline || "") + "";
			var dpac = document.createElement("gmp-place-autocomplete");
			dpac.setAttribute("placeholder", this.settings.routeOptions.placeholder || "Enter departure address");
			dpac.setAttribute("class", "map_direction_input");
			dpac.setAttribute("id", "map_direction_input");
			if (this.settings.routeOptions.country != null && String(this.settings.routeOptions.country).toLowerCase() !== "all")
				dpac.setAttribute("included-region-codes", this.settings.routeOptions.country);
			dpac.setAttribute("included-primary-types", "street_address establishment");
			on(dpac, "gmp-placeselect", function (ev) {
				var place = ev.place;
				if (!place || !place.fetchFields) return;
				place.fetchFields({ fields: ["location"] }).then(function () {
					if (!place.location) return;
					var loc = place.location;
					var lat = loc && (typeof loc.lat === "function" ? loc.lat() : loc.lat);
					var lng = loc && (typeof loc.lng === "function" ? loc.lng() : loc.lng);
					if (lat == null || lng == null) return;
					_t._routeOrigin = { latLng: new google.maps.LatLng(lat, lng) };
					if (_t._routeDestination) {
						_t._directionsDisplay.setMap(_t.map);
						_t._directionsDisplay.setPanel(document.getElementById("map_route"));
						_t._calculateAndDisplayRoute(_t._dirSvc, _t._directionsDisplay, _t._routeOrigin.latLng, _t._routeDestination);
					}
				}).catch(function () {});
			});
			mrd.appendChild(dpac);
			var cl = document.createElement("a");
			cl.href = "#";
			cl.className = "map_direction_close_trigger";
			cl.innerHTML = this.settings.routeOptions.closeHtml || "close";
			mrd.appendChild(cl);
			var res = qs(".map_results");
			if (res) res.appendChild(mrd);
			this._directionsDisplay = new google.maps.DirectionsRenderer();
			this._dirSvc = new google.maps.DirectionsService();
		}

		// Tilesloaded: viewport listeners
		google.maps.event.addListenerOnce(this.map, "tilesloaded", function () {
			if (_t.settings.listOptions.updateOn.zoom)
				_t.zoomListener = google.maps.event.addListener(_t.map, "zoom_changed", _t._getInViewportMarkers.bind(_t));
			if (_t.settings.listOptions.updateOn.drag)
				google.maps.event.addListener(_t.map, "dragend", _t._getInViewportMarkers.bind(_t));
			if (_t.settings.listOptions.updateOn.resize) {
				google.maps.event.addListener(_t.map, "resize", _t._getInViewportMarkers.bind(_t));
				google.maps.event.addDomListener(window, "resize", function () {
					if (_t.settings.defaultLocation == null && _t._bounds) _t.map.fitBounds(_t._bounds);
				});
			}
		});
	};

	MapStoreLocator.prototype._initMarker = function () {
		this._createMarkers();
		if (this.settings.defaultLocation != null) this._initDefaultLocation();
		else {
			if (this.settings.listOptions.sortByDistance) this.map.setCenter(this._bounds.getCenter());
			this.map.fitBounds(this._bounds);
		}
	};

	MapStoreLocator.prototype._latRad = function (lat) {
		var x = Math.sin(lat * Math.PI / 180);
		return Math.max(Math.min(Math.log((1 + x) / (1 - x)) / 2, Math.PI), -Math.PI) / 2;
	};
	MapStoreLocator.prototype._zoom = function (mapPx, worldPx, frac) { return Math.floor(Math.log(mapPx / worldPx / frac) / Math.LN2); };
	MapStoreLocator.prototype._getBoundsZoomLevel = function (bounds, mapDim) {
		var arr = bounds.split(",");
		var latF = (this._latRad(parseFloat(arr[2])) - this._latRad(parseFloat(arr[0]))) / Math.PI;
		var lngD = parseFloat(arr[3]) - parseFloat(arr[1]);
		var lngF = (lngD < 0 ? lngD + 360 : lngD) / 360;
		return Math.min(this._zoom(mapDim.height, 256, latF), this._zoom(mapDim.width, 256, lngF), 18);
	};

	MapStoreLocator.prototype._initDefaultLocation = function () {
		var loc = this.settings.defaultLocation, latLng;
		if (Array.isArray(loc)) latLng = new google.maps.LatLng(loc[0], loc[1]);
		else return;
		this.map.setCenter(latLng);
		var mc = qs(".map_container");
		var dim = { height: mc ? mc.getBoundingClientRect().height : 400, width: mc ? mc.getBoundingClientRect().width : 600 };
		var z = this._getBoundsZoomLevel(this.settings.viewport, dim);
		this.settings.mapOptions.zoom = z;
		this.map.setZoom(z);
		var _t = this;
		this._boundInitListener = google.maps.event.addListener(this.map, "bounds_changed", function () { _t._getInViewportMarkers(); });
	};

	MapStoreLocator.prototype._initClicks = function () {
		var _ = this;

		// .result_item > a: open detail (by data-id from Alpine-rendered list)
		on(document, "click", function (e) {
			var a = e.target.closest(".result_item > a");
			if (!a) return;
			var ri = e.target.closest(".result_item");
			if (!ri || !ri.dataset.id) return;
			e.preventDefault();
			var d = _._findById(ri.dataset.id);
			if (d) _._updateDetail(d);
		});

		on(document, "click", function (e) {
			if (!e.target.closest(".filter_minimize")) return;
			var n = document.getElementById("mapFilterNavigation");
			if (!n) return;
			if (_._filterNavigationHeight == null) _._filterNavigationHeight = n.offsetHeight;
			if (n.classList.contains("minimized")) { n.style.height = _._filterNavigationHeight + "px"; n.classList.remove("minimized"); }
			else { n.style.height = e.target.offsetHeight + "px"; n.classList.add("minimized"); }
		});

		on(document, "click", function (e) {
			if (!e.target.closest(".map_search_icon")) return;
			var fi = qs(".map_filter_input");
			if (fi) fi.classList.toggle("input_open");
		});

		on(document, "keyup", function (e) {
			if (e.target.id !== "search") return;
			var val = (e.target.value || "").trim();
			qsAll(".map_listings_results .result_item").forEach(function (el) {
				el.style.display = val && el.textContent.indexOf(val) < 0 ? "none" : "";
			});
		});

		// Route: map_direction_trigger (get directions in list or detail)
		on(document, "click", function (e) {
			var tr = e.target.closest(".map_direction_trigger");
			if (!tr) return;
			var mrt = qs(".map_route");
			if (!mrt || mrt.classList.contains("open")) return;
			mrt.classList.add("open");
			e.preventDefault();
			var destData = null;
			var ri = e.target.closest(".result_item");
			if (ri && ri.dataset.id) destData = _._findById(ri.dataset.id);
			if (!destData) {
				var s = _._getStore();
				if (s && s.detail) destData = s.detail;
			}
			if (destData) {
				_._routeDestination = destData.location.latitude + "," + destData.location.longitude;
				var orig = _._routeOrigin && _._routeOrigin.latLng ? _._routeOrigin.latLng : null;
				if (orig && _._dirSvc && _._directionsDisplay) {
					_._directionsDisplay.setMap(_.map);
					_._directionsDisplay.setPanel(document.getElementById("map_route"));
					_._calculateAndDisplayRoute(_._dirSvc, _._directionsDisplay, orig, _._routeDestination);
				}
			}
		});

		on(document, "click", function (e) {
			if (e.target.closest(_.settings.detailsOptions.closeTrigger)) { e.preventDefault(); _.closeDetail(); }
		});

		on(document, "click", function (e) {
			if (!e.target.closest(".map_direction_close_trigger")) return;
			_._closeDirections();
		});

		// Detail slider: .next / .prev in .result_item_detail_info .slider_container
		on(document, "click", function (e) {
			var next = e.target.closest(".result_item_detail_info .slider_container .next");
			var prev = e.target.closest(".result_item_detail_info .slider_container .prev");
			if (!next && !prev) return;
			var container = (next || prev).closest(".slider_container");
			if (!container) return;
			var items = container.querySelectorAll("> div");
			if (items.length === 0) return;
			var current = 0;
			for (var i = 0; i < items.length; i++) {
				var ds = items[i].style.display;
				if (ds && ds !== "none") { current = i; break; }
			}
			if (next) current = current >= items.length - 1 ? 0 : current + 1;
			else current = current <= 0 ? items.length - 1 : current - 1;
			for (var j = 0; j < items.length; j++) items[j].style.display = j === current ? "inline-block" : "none";
		});

		// Categories (if used)
		on(document, "click", function (e) {
			var a = e.target.closest(".categories a");
			if (!a) return;
			e.preventDefault();
			if (a.classList.contains("map-marker-filter-all")) {
				qsAll(".categories a").forEach(function (x) { if (x !== a) x.classList.remove("active"); });
				a.classList.add("active");
				_._activeCategories = [];
			} else {
				var c = a.dataset.cat;
				if (a.classList.contains("active")) {
					_._activeCategories = _._activeCategories.filter(function (v) { return v !== c; });
					a.classList.remove("active");
				} else {
					_._activeCategories = _._activeCategories.concat([c]);
					a.classList.add("active");
				}
			}
			_._createMarkers();
			if (_.settings.categoriesOptions.boundOnClick) {
				if (_.settings.listOptions.updateOn.zoom && _.zoomListener) google.maps.event.removeListener(_.zoomListener);
				_.map.fitBounds(_._bounds);
				_._initList();
				if (_.settings.listOptions.updateOn.zoom) _.zoomListener = google.maps.event.addListener(_.map, "zoom_changed", _._getInViewportMarkers.bind(_));
			} else {
				_._getInViewportMarkers();
			}
		});

		// Hover: .result_item -> bounce; mouseout from list item -> stop marker
		on(document, "mouseenter", function (e) {
			var ri = e.target.closest(".result_item");
			if (!ri || !ri.dataset.id) return;
			var m = _._markers[ri.dataset.id];
			if (m && m.setAnimation) { m.setAnimation(google.maps.Animation.BOUNCE); setTimeout(function () { if (m.setAnimation) m.setAnimation(null); }, 750); }
		});
		on(document, "mouseout", function (e) {
			var ri = e.target.closest && e.target.closest(".result_item");
			if (ri && ri.dataset.id) {
				if (!e.relatedTarget || !e.relatedTarget.closest || !e.relatedTarget.closest(".result_item")) {
					var m = _._markers[ri.dataset.id];
					if (m && m.setAnimation) m.setAnimation(null);
				}
			}
			if (!e.relatedTarget || !e.relatedTarget.closest) return;
			if (e.relatedTarget.closest(".result_item")) return;
			qsAll(".map_listings_results .result_item").forEach(function (el) { el.classList.remove("active"); });
		});
	};

	MapStoreLocator.prototype._geolocationSuccess = function (position) {
		this.map.setCenter(new google.maps.LatLng(position.coords.latitude, position.coords.longitude));
		this.map.setZoom(this.settings.geoLocationOptions.zoom);
	};
	MapStoreLocator.prototype._geolocationError = function (msg) { this._showNotification(msg); };

	MapStoreLocator.prototype._createMarkers = function () {
		this._removeMarkers();
		var bounds = new google.maps.LatLngBounds();
		var BLA = typeof window.BLA !== "undefined" ? window.BLA : "";
		var filter = this._activeCategories;
		var catField = this.settings.categoriesOptions.categoryField;
		var icons = this.settings.categoriesOptions.icons;

		for (var x = 0; x < this.stores.length; x++) {
			var data = this.stores[x];
			var cname = data[catField];
			if (filter && filter.length > 0 && filter.indexOf(cname) === -1) continue;
			this._showData.push(data);
			var ico = (icons && icons[cname]) ? icons[cname] : (this.settings.markerOptions.markerIcon || BLA);
			var latLng = new google.maps.LatLng(data.location.latitude, data.location.longitude);
			var marker = new google.maps.Marker({ position: latLng, map: this.map, icon: ico, draggable: this.settings.markerOptions.draggable, itemId: data.id });

			var trimmed = encodeURIComponent((data.meeting_address || "").trim());
			var url = (data.url && data.url.trim()) ? data.url.trim() : "";
			var more = url ? '<a class="label label-success label-map" href="' + url + '">more info</a>' : "";
			var content = "<b><h6>Church in " + (data.locality_name || "") + "</h6></b>" + (data.meeting_address || "") + "<br>" + more + '<a class="label label-danger label-map" href="https://maps.google.com/?saddr=Current%20Location&daddr=' + trimmed + '">get directions here</a>';
			var _map = this.map;
			var self = this;
			google.maps.event.addListener(marker, "click", function () {
				if (self.infowindow) self.infowindow.close();
				self.infowindow.setContent(content);
				self.infowindow.open(_map, marker);
			});
			if (this.settings.markerOptions.dropAnimation && marker.setAnimation) marker.setAnimation(google.maps.Animation.DROP);
			google.maps.event.addListener(marker, "click", this._handleMarkerClick.bind(this, marker, data));
			google.maps.event.addListener(marker, "mouseover", this._handleMarkerMouseover.bind(this, marker, data));
			google.maps.event.addListener(marker, "mouseout", function () {
				qsAll(".map_listings_results .result_item").forEach(function (el) { el.classList.remove("active"); });
			});
			this._markers[data.id] = marker;
			this.markers.push(marker);
			bounds.extend(latLng);
		}
		this._bounds = bounds;
		if (this.settings.markerCluster.cluster && typeof MarkerClusterer !== "undefined")
			this._markerCluster = new MarkerClusterer(this.map, this.markers, { imagePath: this.settings.markerCluster.imagePath, cssClass: this.settings.markerCluster.cssClass });
	};

	MapStoreLocator.prototype._handleMarkerClick = function (marker, data) {
		if (typeof this.settings.onBeforeClickMarker === "function") this.settings.onBeforeClickMarker.call(this, data);
		this._updateDetail(data);
		if (this.settings.routeOptions.show) this._closeDirections();
	};

	MapStoreLocator.prototype._handleMarkerMouseover = function (marker, data) {
		var el = document.querySelector('[data-id="' + data.id + '"]');
		if (el) el.classList.add("active");
	};

	MapStoreLocator.prototype._getInViewportMarkers = function () {
		this.viewPortMarkers = [];
		for (var i = 0; i < this.markers.length; i++) {
			if (this.map.getBounds() && this.map.getBounds().contains(this.markers[i].getPosition()))
				this.viewPortMarkers[i] = this.markers[i].itemId;
		}
		if (this._boundInitListener) { google.maps.event.removeListener(this._boundInitListener); this._boundInitListener = null; }
		this._updateList();
	};

	MapStoreLocator.prototype._removeMarkers = function () {
		for (var i = 0; i < this.markers.length; i++) {
			var m = this.markers[i];
			if (m.setMap) m.setMap(null);
		}
		if (this._markerCluster) { this._markerCluster.clearMarkers(); this._markerCluster = null; }
		this.markers = [];
		this._markers = {};
	};

	MapStoreLocator.prototype._sortByDistance = function (a, b) { return (parseFloat(a.distance) || 0) - (parseFloat(b.distance) || 0); };

	MapStoreLocator.prototype._initList = function () {
		var list = this._showData.slice();
		if (this.settings.listOptions.sortByDistance) {
			var c = this.map.getCenter();
			var center = new google.maps.LatLng(c.lat(), c.lng());
			var dist = this.settings.listOptions.distanceType === "miles" ? 0.000621371192 : 1 / 1000;
			for (var k = 0; k < list.length; k++) {
				var L = new google.maps.LatLng(list[k].location.latitude, list[k].location.longitude);
				var d = google.maps.geometry.spherical.computeDistanceBetween(center, L);
				list[k].distance = (d * dist).toFixed(1);
			}
			list.sort(this._sortByDistance.bind(this));
		}
		this._pushList(list);
		if (typeof this.settings.onUpdateList === "function") {
			var self = this;
			setTimeout(function () { self.settings.onUpdateList.call(self); }, 0);
		}
	};

	MapStoreLocator.prototype._updateList = function () {
		var data = this._showData;
		var view = this.viewPortMarkers || [];
		var listItems = [];
		var center = null;
		if (this.settings.listOptions.sortByDistance) center = new google.maps.LatLng(this.map.getCenter().lat(), this.map.getCenter().lng());
		var dist = this.settings.listOptions.distanceType === "miles" ? 0.000621371192 : 1 / 1000;

		for (var i = 0; i < view.length; i++) {
			for (var k = 0; k < data.length; k++) {
				if (view[i] !== data[k].id) continue;
				if (center) {
					var L = new google.maps.LatLng(data[k].location.latitude, data[k].location.longitude);
					data[k].distance = (google.maps.geometry.spherical.computeDistanceBetween(center, L) * dist).toFixed(1);
				}
				listItems.push(data[k]);
			}
		}
		if (this.settings.listOptions.sortByDistance) listItems.sort(this._sortByDistance.bind(this));
		this._pushList(listItems);
		if (typeof this.settings.onUpdateList === "function") this.settings.onUpdateList.call(this, data);
	};

	MapStoreLocator.prototype._updateDetail = function (data) {
		this._pushDetail(data);
		if (this.settings.detailsOptions.panorama.showPanorama) {
			var sv = new google.maps.StreetViewService();
			var ll = new google.maps.LatLng(data.location.latitude, data.location.longitude);
			var pan = this.settings.detailsOptions.panorama;
			sv.getPanorama({ location: ll, radius: pan.searchRadius }, function (d, status) {
				var c = document.getElementById(pan.container);
				if (status === google.maps.StreetViewStatus.OK && c) {
					var p = new google.maps.StreetViewPanorama(c);
					p.setPano(d.location.pano);
					p.setPov({ heading: 270, pitch: 0 });
					p.setVisible(true);
				} else if (c) {
					c.style.backgroundColor = "transparent";
					c.style.height = "auto";
					c.style.width = "100%";
					c.innerHTML = pan.notFoundText;
				}
			});
		}
		if (typeof this.settings.onUpdateDetail === "function") this.settings.onUpdateDetail.call(this, data);
	};

	MapStoreLocator.prototype.closeDetail = function () { this._clearDetail(); };

	MapStoreLocator.prototype._calculateAndDisplayRoute = function (svc, disp, start, end) {
		var _ = this;
		svc.route({ origin: start, destination: end, travelMode: google.maps.TravelMode.DRIVING }, function (res, status) {
			if (status === google.maps.DirectionsStatus.OK) disp.setDirections(res);
			else _._showNotification("Directions request failed due to " + status);
		});
	};

	MapStoreLocator.prototype._closeDirections = function () {
		var mrt = qs(".map_route");
		if (mrt && mrt.classList.contains("open")) {
			mrt.classList.remove("open");
			if (this._directionsDisplay) this._directionsDisplay.setMap(null);
		}
	};

	MapStoreLocator.prototype._showNotification = function (msg) {
		var c = qs(".map_container");
		if (!c) return;
		var d = document.createElement("div");
		d.id = "map_notification";
		d.className = this.settings.notificationOptions.class || "";
		d.textContent = msg;
		c.appendChild(d);
		d.style.display = "";
		var self = this;
		setTimeout(function () {
			var n = document.getElementById("map_notification");
			if (n) n.remove();
		}, this.settings.notificationOptions.duration || 5000);
	};

	MapStoreLocator.prototype._initResponsive = function () {
		var w = window.innerWidth || document.documentElement.clientWidth || 0;
		var h = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
		var mw = qs(".map_wrapper");
		var mc = qs(".map_container");
		var mr = qs(".map_results");
		if (!mw || !mc || !mr) return;
		var ro = this.settings.responsiveOptions || [];
		var bp = 0;
		for (var i = 0; i < ro.length; i++) if (w <= ro[i].breakpoint) bp = ro[i].breakpoint;
		var settings = null;
		for (var j = 0; j < ro.length; j++) if (ro[j].breakpoint === bp) { settings = ro[j].settings; break; }
		if (!settings) {
			if (this.settings.height) mw.style.height = this.settings.height;
			else mw.style.height = h + "px";
			mc.style.height = "100%";
			mr.style.height = "100%";
		} else {
			mw.style.height = "auto";
			var mh = settings.mapHeight === "full" ? h : (settings.mapHeight || 400);
			mc.style.height = (typeof mh === "number" ? mh + "px" : mh);
			mr.style.height = (typeof settings.listHeight === "number" ? settings.listHeight + "px" : (settings.listHeight || "400px"));
		}
	};

	window.mapStoreLocator = {
		init: function (element, options) {
			return new MapStoreLocator(element, options);
		}
	};
})(window, document);
