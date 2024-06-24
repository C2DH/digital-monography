/** LibLynx COUNTER Release 5 Tracker v1.0.7
 * (c) 2023 LibLynx LLC
 * @preserve
 */
!function() {
    "use strict";
    function LLTracker() {
        var context = this;
        this.option = [];
        this.endpoint = "//connect.liblynx.com/log/counter";
        this.defaults = {};
        function error(msg) {
            var c = "consol" + String.fromCharCode(101);
            window[c].error(msg);
        }
        function base64_encode(input) {
            var chr1, chr3, enc1, enc2, enc3, enc4, j, bytes, _keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=", output = "", bin = "", i = 0;
            if (void 0 !== window.TextDecoder && void 0 !== window.btoa) {
                bytes = new TextEncoder().encode(input);
                for (j = 0; j < bytes.length; j++) bin += String.fromCodePoint(bytes[j]);
                return btoa(bin);
            }
            input = function(string) {
                string = string.replace(/\r\n/g, "\n");
                for (var c, utftext = "", n = 0; n < string.length; n += 1) (c = string.charCodeAt(n)) < 128 ? utftext += String.fromCharCode(c) : utftext = 127 < c && c < 2048 ? (utftext += String.fromCharCode(c >> 6 | 192)) + String.fromCharCode(63 & c | 128) : (utftext = (utftext += String.fromCharCode(c >> 12 | 224)) + String.fromCharCode(c >> 6 & 63 | 128)) + String.fromCharCode(63 & c | 128);
                return utftext;
            }(input);
            for (;i < input.length; ) {
                enc1 = (chr1 = input.charCodeAt(i++)) >> 2;
                enc2 = (3 & chr1) << 4 | (chr1 = input.charCodeAt(i++)) >> 4;
                enc3 = (15 & chr1) << 2 | (chr3 = input.charCodeAt(i++)) >> 6;
                enc4 = 63 & chr3;
                isNaN(chr1) ? enc3 = enc4 = 64 : isNaN(chr3) && (enc4 = 64);
                output = output + _keyStr.charAt(enc1) + _keyStr.charAt(enc2) + _keyStr.charAt(enc3) + _keyStr.charAt(enc4);
            }
            return output;
        }
        function logHit(type, metadata) {
            metadata.type = type;
            var xhr, type = JSON.stringify(metadata), image = new Image(1, 1), type = base64_encode(type), type = context.endpoint + "?j=" + window.escape(type) + "&r=" + Math.random();
            if (metadata.hasOwnProperty("sync")) {
                (xhr = new XMLHttpRequest()).open("GET", type, !1);
                xhr.send(null);
            } else image.src = type;
            !function(payload) {
                if (void 0 !== window.sessionStorage && window.sessionStorage.getItem("llqa")) {
                    if (!window.sessionStorage.getItem("llcount")) {
                        window.sessionStorage.setItem("llcount", "0");
                        window.sessionStorage.setItem("llevents", "[]");
                    }
                    window.sessionStorage.setItem("llcount", parseInt(window.sessionStorage.getItem("llcount"), 10) + 1);
                    var events = [];
                    try {
                        events = JSON.parse(window.sessionStorage.getItem("llevents"));
                    } catch (e) {
                        context.warn("QA events cleared");
                    }
                    events.push(payload);
                    window.sessionStorage.setItem("llevents", JSON.stringify(events));
                }
            }(metadata);
        }
        function checkStandardTrackingData(metadata) {
            var ok = 1;
            !function(metadata) {
                for (var property in context.defaults) context.defaults.hasOwnProperty(property) && !metadata.hasOwnProperty(property) && (metadata[property] = context.defaults[property]);
            }(metadata);
            if (void 0 === metadata.pid) {
                error("Must use _ll.push('setProviderId', ...) or _ll.push('setDefaults', {pid:'...'}) before tracking activity, or include pid value in metadata");
                ok = 0;
            }
            if (void 0 !== metadata.llid) ok = 1; else if (void 0 !== metadata.aid) {
                void 0 === metadata.sid && console.warn("tracking call missing sid (session id) - one will by synthesized by LibLynx");
                void 0 === metadata.aname && console.warn("tracking call missing aname (account name) - this is required if account names have not been synchronized with a bulk-import. Otherwise, you can set aname:false to suppress this warning");
                "_oa" === metadata.aid && (metadata.anon = !0);
            } else if (void 0 !== metadata.anon && !0 === metadata.anon) ok = 1; else {
                error("object passed to tracking API expected to have either aid or llid members, or set anon:true for open access analytics where account is not known");
                ok = 0;
            }
            void 0 === metadata.url && (metadata.url = window.location.href);
            return ok;
        }
        this.exec = function(args) {
            var method = args.shift();
            context[method] ? context[method].apply(context, args) : error("Unknown LibLynx Tracker method " + method);
        };
        this.setDefaults = function(defaults) {
            var property, t;
            for (property in defaults) if (defaults.hasOwnProperty(property) && ("string" == (t = typeof defaults[property]) || "number" == t)) {
                this.verbose("Default " + property + " = " + defaults[property]);
                this.defaults[property] = defaults[property];
            }
        };
        this.enableQAMode = function() {
            void 0 !== window.sessionStorage && window.sessionStorage.setItem("llqa", "1");
        };
        this.setProviderId = function(providerId) {
            this.verbose("setProviderId(" + providerId + ")");
            this.defaults.pid = providerId;
        };
        this.setResourceId = function(resourceId) {
            this.verbose("setResourceId(" + resourceId + ")");
            this.defaults.rid = resourceId;
        };
        this.setEndpoint = function(url) {
            this.verbose("setEndpoint(" + url + ")");
            this.endpoint = url;
        };
        this.setOption = function(name, value) {
            this.option[name] = value = void 0 === value || value;
            this.verbose("setOption " + name + "=" + value);
        };
        this.verbose = function() {
            this.option.verbose && console.log(arguments);
        };
        this.warn = function() {
            this.option.verbose && console.warn(arguments);
        };
        this.trackOpenAccessRequest = function(metadata) {
            this.verbose("trackOpenAccessRequest", metadata);
            (metadata = void 0 === metadata ? {} : metadata).anon = !0;
            checkStandardTrackingData(metadata) && logHit("ir", metadata);
        };
        this.trackRequest = function(metadata) {
            this.trackItemRequest(metadata);
        };
        this.trackItemRequest = function(metadata) {
            this.verbose("trackRequest", metadata);
            checkStandardTrackingData(metadata = void 0 === metadata ? {} : metadata) && logHit("ir", metadata);
        };
        this.trackInvestigation = function(metadata) {
            this.trackItemInvestigation(metadata);
        };
        this.trackItemInvestigation = function(metadata) {
            this.verbose("trackInvestigation", metadata);
            checkStandardTrackingData(metadata = void 0 === metadata ? {} : metadata) && logHit("ii", metadata);
        };
        this.trackSearch = function(metadata) {
            this.verbose("trackSearch", metadata);
            checkStandardTrackingData(metadata = void 0 === metadata ? {} : metadata) && logHit("se", metadata);
        };
        this.trackDenial = function(metadata) {
            this.verbose("trackDenial", metadata);
            checkStandardTrackingData(metadata = void 0 === metadata ? {} : metadata) && logHit("de", metadata);
        };
        this.trackOAView = function(metadata) {
            this.verbose("trackOAView", metadata);
            checkStandardTrackingData(metadata = void 0 === metadata ? {} : metadata) && logHit("oa", metadata);
        };
        this.trackRecordView = function(metadata) {
            this.warn("trackRecordView - COUNTER release 4 tracking ignored consider trackItemRequest", metadata);
        };
        this.trackRegularSearch = function(metadata) {
            this.warn("trackRegularSearch - COUNTER release 4 tracking ignored, consider trackSearch", metadata);
        };
        this.trackResultClick = function(metadata) {
            this.warn("trackResultClick - COUNTER release 4 tracking ignored, consider trackItemInvestigation", metadata);
        };
        this.trackBrowseClick = function(metadata) {
            this.warn("trackBrowseClick - COUNTER release 4 tracking ignored, consider trackItemInvestigation", metadata);
        };
        this.trackBrowseSearch = function(metadata) {
            this.warn("trackBrowseSearch - COUNTER release 4 tracking ignored", metadata);
        };
        this.trackMultimediaContentUnit = function(metadata) {
            this.warn("trackMultimediaContentUnit - COUNTER release 4 tracking ignored, consider trackItemRequest", metadata);
        };
        this.trackDatabaseLicenceDenial = function(metadata) {
            this.warn("trackDatabaseLicenceDenial - COUNTER release 4 tracking ignored, consider trackDenial", metadata);
        };
        this.trackDatabaseConcurrencyDenial = function(metadata) {
            this.warn("trackDatabaseConcurrencyDenial - COUNTER release 4 tracking ignored, consider trackDenial", metadata);
        };
        this.trackJournalArticle = function(metadata) {
            this.warn("trackJournalArticle - COUNTER release 4 tracking ignored, consider trackItemRequest", metadata);
        };
        this.trackBook = function(metadata) {
            this.warn("trackBook - COUNTER release 4 tracking ignored, consider trackItemRequest", metadata);
        };
    }
    Array.isArray(window._ll) && (window._ll = new function(queue) {
        for (var cmd, tracker = new LLTracker(); queue.length; ) {
            cmd = queue.shift();
            tracker.exec(cmd);
        }
        this.push = function(argArray) {
            return tracker.exec(argArray);
        };
    }(window._ll));
}();