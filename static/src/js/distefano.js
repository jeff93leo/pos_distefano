openerp.pos_distefano = function(instance){
    var module = instance.point_of_sale;
    var QWeb = instance.web.qweb;
    
    // var displayBox =function(){
    //     var date = new Date();
    //     var hrs = date.getHours();
    //     var min= date.getMinutes();
    //     if ( (hrs==19 && (min>=30 || min<=31)) || (hrs==20 && (min>=15 || min<=16))){
    //         window.alert('--------NO OLVIDE CERRAR SU SESIÓN POR FAVOR, GRACIAS.--------');
    //     }
    // }
    // setInterval(displayBox,100000);
    
    var mixAndMatch = function(orden) {
        var lineas = orden.get('orderLines')['models'];

        if (lineas.length > 0) {

            var productos = [];
            var cantidad = 0;

            lineas.forEach(function(l) {

                if (l.product.pos_categ_id) {
                    return;
                }

                // Para evitar que si se hace el mix and mach nuevamente
                // se haga un doble descuento.
                if (!("precio_original" in l)) {
                    l['precio_original'] = l.get_unit_price();
                }
                for (i = 0; i < l.get_quantity(); i++) {
                    productos.push({'linea': l, 'precio': l['precio_original'], 'precio_original': l['precio_original']});
                }
                cantidad += l.get_quantity();
            })

            productos.sort(function(a, b) {
                return a['precio'] - b['precio'];
            })

            var restantes = Math.floor(cantidad / 2);
            var incremento = Math.ceil(cantidad / 2);
            for (i = 0; i < restantes; i++) {
                var descuento = productos[i]['precio'];
                var total = productos[i]['precio'] + productos[i+incremento]['precio'];
                productos[i]['precio'] = productos[i]['precio'] - ( productos[i]['precio'] / total * descuento );
                productos[i+incremento]['precio'] = productos[i+incremento]['precio'] - ( productos[i+incremento]['precio'] / total * descuento );
            }

            productos.forEach(function(p) {
                // Si este producto no cambio de precio es por que es
                // uno impar, por lo que tiene un 25% de descuento
                var precio = p['precio'];
                if (p['precio'] == p['precio_original']) {
                    precio = p['precio'] * 0.75;
                }

                var l = p['linea'].clone();
                l.set_quantity(1);
                l.set_unit_price(precio);

                l['precio_original'] = p['precio_original'];
                orden.addOrderline(l);
            })

            productos.forEach(function(p) {
                orden.removeOrderline(p['linea']);
            })
        }
    }

    var bancoIndustrial = function(orden) {
        var lineas = orden.get('orderLines')['models'];

        if (lineas.length > 0) {

            var productos = [];
            var cantidad = 0;

            lineas.forEach(function(l) {

                // Para evitar que si se hace el mix and mach nuevamente
                // se haga un doble descuento.
                if (!("precio_original" in l)) {
                    l['precio_original'] = l.get_unit_price();
                }
                for (i = 0; i < l.get_quantity(); i++) {
                    productos.push({'linea': l, 'precio': l['precio_original'], 'precio_original': l['precio_original']});
                }
                cantidad += l.get_quantity();
            })

            productos.sort(function(a, b) {
                return a['precio'] - b['precio'];
            })

            productos.forEach(function(p) {
                //Tiene un 60% de descuento
                var precio = p['precio'] * 0.40;
                var l = p['linea'];
                l.set_quantity(1);
                l.set_unit_price(precio);

            })
        }
    }

    QWeb.add_template('/pos_distefano/static/src/xml/distefano.xml');

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();

            // //boton de Mix & Match
            // var distefanoMixMatch = $('#DistefanoMixMatch');
            // distefanoMixMatch.click(function() {
            //     var orden = self.pos.get('selectedOrder');
            //     mixAndMatch(orden);
            // });
            
            // distefanoMixMatch.appendTo(this.$('.control-buttons-dinamica'));

            // // boton de Banco Industrial
            // var bancoBi = $('#BI');
            // bancoBi.click(function() {
            //     window.prompt("Favor ingresar los ultimos 4 digitos de la tarjeta","****");
            //     var orden = self.pos.get('selectedOrder');
            //     bancoIndustrial(orden);
            //     $('#dinamica').prop('checked', true);
            // });

            // bancoBi.appendTo(this.$('.control-buttons-dinamica'));

            var distefanoVendedores = $(QWeb.render('DistefanoVendedores'));
            var select = distefanoVendedores.find("select");
            self.pos.users.forEach(function(e, i) {
                if (e.ean13) {
                    select.append(this.$("<option></option>").val(i).html(e.name));
                }
            })
            select.change(function() {
                var i = select.find("option:selected").val();
                self.pos.cashier = self.pos.users[i];
                self.pos_widget.username.refresh();
            })

            distefanoVendedores.appendTo(this.$('.control-buttons'));
            this.$('.control-buttons').removeClass('oe_hidden');
        },
    });
    
    module.Order = module.Order.extend( {
        getTotalQuantity: function() {
            return (this.get('orderLines')).reduce((function(sum, orderLine) {
                return sum + orderLine.get_quantity();
            }), 0);
        },
        getTicket: function() {
            var contador = 0;
            var cantidad =  $("#cantidad_gift");
            var arreglo = new Array(cantidad.val());
            for (var i = 0; i < cantidad.val(); i++) {
                contador = contador + 1;
                arreglo[i] = contador;
            }
            return arreglo;
        },
        // getBi: function(){
        //     var dinamica = $('#dinamica').prop("checked");
        //     return dinamica;
        // }        
    });

    module.OrderWidget = module.OrderWidget.extend({
        update_summary: function(){
            var order = this.pos.get('selectedOrder');
            var total     = order ? order.getTotalTaxIncluded() : 0;
            var taxes     = order ? total - order.getTotalTaxExcluded() : 0;
            var quantity  = order ? order.getTotalQuantity() : 0;

            this.el.querySelector('.summary .total .quantity').textContent = quantity;
            this.el.querySelector('.summary .total .value').textContent = this.format_currency(total);
            this.el.querySelector('.summary .total .subentry .value').textContent = this.format_currency(taxes); 
        },
    });
    
    var _super_add_product = module.Order.prototype.addProduct;
    module.Order.prototype.addProduct = function(product, options) {
        _super_add_product.call(this, product, options);

        var orden = this.pos.get('selectedOrder');
        mixAndMatch(orden);
    }

    var _super_export_as_JSON = module.Order.prototype.export_as_JSON;
    module.Order.prototype.export_as_JSON = function() {
        var JSON = _super_export_as_JSON.call(this);

        var pad = Array(this.pos.config.relleno+1).join("0");
        var num = this.pos.config.numero_siguiente+this.pos.config.pedidos_pendientes;
        var num = ""+num;
        var bi=$('#dinamica').prop("checked");
        JSON['dinamica'] =bi;
        JSON['numero_factura'] = this.pos.config.prefijo+pad.substring(num.length) + num;
        this.dinamica = JSON['dinamica'];
        this.numero_factura = JSON['numero_factura'];
        return JSON;
    }

    var _super_push_order = module.PosModel.prototype.push_order;
    module.PosModel.prototype.push_order = function(order) {
        var pushed = _super_push_order.call(this, order);

        var pad = Array(this.config.relleno+1).join("0");
        var num = this.config.numero_siguiente+this.config.pedidos_pendientes;
        var num = ""+num;
        var dinamica = $('#dinamica').prop("checked");
        $('#dinamica').prop("checked",dinamica);
        var siguiente_factura = this.config.prefijo+pad.substring(num.length) + num
        $('#factura-siguiente').text(siguiente_factura+'.');
        console.log($('#factura-siguiente'));

        return pushed;
    }

    var _super_display_client_details = module.ClientListScreenWidget.prototype.display_client_details;
    module.ClientListScreenWidget.prototype.display_client_details = function(visibility,partner,clickpos) {
        var pushed = _super_display_client_details.call(this, visibility,partner,clickpos);
        if (visibility === 'edit') {
            var vat = this.$('.screen-content input').val();
            this.$('.vat').val(vat);
        };
    }

    var _super_show = module.ClientListScreenWidget.prototype.show;
    module.ClientListScreenWidget.prototype.show = function(){
        var pushed = _super_show.call(this);
        this.$('.searchbox input').focus();
    }

    var _super_renderElement = module.ProductCategoriesWidget.prototype.renderElement;
    module.ProductCategoriesWidget.prototype.renderElement = function(){
        var pushed = _super_renderElement.call(this);
        this.el.querySelector('.searchbox input').focus();
    }

    var _super_display_checkbox = module.PaymentScreenWidget.prototype.update_payment_summary;
    module.PaymentScreenWidget.prototype.update_payment_summary = function(){
        _super_display_checkbox.call(this);
        // $('#dinamica').show();
        $("#cantidad_gift").hide();
        this.$("#squaredFour").click(function(){
            if(this.checked){
                $("#cantidad_gift").show();
            }else{
                $("#cantidad_gift").hide();
            }
        });     
    }

    QWeb.add_template('/pos_distefano/static/src/xml/facturas.xml');
    module.ReceiptScreenWidget.include({
        refresh: function() {
            var order = this.pos.get('selectedOrder');
            $('.pos-receipt-container', this.$el).html(QWeb.render('PosTicket',{
                    widget:this,
                    order: order,
                    orderlines: order.get('orderLines').models,
                    paymentlines: order.get('paymentLines').models,
                }));
            $('.pos-receipt-container-p', this.$el).html(QWeb.render('PosTicket1',{
                    widget:this,
                    order: order,
                    orderlines: order.get('orderLines').models,
                    paymentlines: order.get('paymentLines').models,
                }));
            $('.pos-receipt-container-p2', this.$el).html(QWeb.render('PosTicket2',{
                    widget:this,
                    order: order,
                    orderlines: order.get('orderLines').models,
                    paymentlines: order.get('paymentLines').models,
                }));
            $('.pos-receipt-container-p3', this.$el).html(QWeb.render('PosTicket3',{
                    widget:this,
                    order: order,
                    orderlines: order.get('orderLines').models,
                    paymentlines: order.get('paymentLines').models,
                }));
        }
    })

    // busqueda busqueda tpv cliente por nit, direccion, nombre..
    module.PosDB.include({
        _partner_search_string: function(partner){
            var str =  partner.name;
            if(partner.ean13){
                str += '|' + partner.ean13;
            }
            if(partner.address){
                str += '|' + partner.address;
            }
            if(partner.phone){
                str += '|' + partner.phone.split(' ').join('');
            }
            if(partner.mobile){
                str += '|' + partner.mobile.split(' ').join('');
            }
            if(partner.email){
                str += '|' + partner.email;
            }
            if(partner.vat){
                str += '|' + partner.vat;

            }
            str = '' + partner.id + ':' + str.replace(':','') + '\n';
            return str;
        }
    })

};
