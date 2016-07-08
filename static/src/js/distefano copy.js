openerp.pos_distefano = function(instance){
    var module = instance.point_of_sale;
    var QWeb = instance.web.qweb;
    console.log(module);

    QWeb.add_template('/pos_distefano/static/src/xml/distefano.xml');

    module.PosWidget.include({
        build_widgets: function(){
            var self = this;
            this._super();

            var distefanoButton = $(QWeb.render('DistefanoButton'));
            var distefanoPaymentReference = $(QWeb.render('DistefanoPaymentReference'));

            distefanoButton.click(function(){
                var orden = self.pos.get('selectedOrder');
                var lineas = orden.get('orderLines')['models'];

                if (lineas.length > 0) {

                    var productos = [];
                    var cantidad = 0;

                    lineas.forEach(function(l, i) {
                        productos.push({'linea':i, 'precio':l.get_unit_price(), 'cantidad':l.get_quantity()});
                        cantidad += l.get_quantity();
                    })

                    productos.sort(function(a, b) {
                        return a['precio'] - b['precio'];
                    })

                    var descuento = 0;
                    var restantes = Math.floor(cantidad / 2);
                    productos.forEach(function(p) {
                        if (restantes < 1) {
                            return;
                        }

                        if (p['cantidad'] <= restantes) {
                            descuento += lineas[p['linea']].get_unit_price() * lineas[p['linea']].get_quantity();
                        } else {
                            descuento += lineas[p['linea']].get_unit_price() * restantes;
                        }
                        restantes -= p['cantidad'];
                    })

                    var precio_unitario = (orden.getTotalTaxIncluded() - descuento) / cantidad

                    lineas.forEach(function(l, i) {
                        l.set_unit_price(precio_unitario)
                    })
                }
            });

            // distefanoButton.click(function(){
            //     var orden = self.pos.get('selectedOrder');
            //     var lineas = orden.get('orderLines')['models'];
            //
            //     if (lineas.length > 0) {
            //
            //         var productos = [];
            //         var cantidad = 0;
            //
            //         lineas.forEach(function(l, i) {
            //             productos.push({'linea':i, 'precio':l.get_unit_price(), 'cantidad':l.get_quantity()});
            //             cantidad += l.get_quantity();
            //         })
            //
            //         productos.sort(function(a, b) {
            //             return a['precio'] - b['precio'];
            //         })
            //
            //         var restantes = Math.floor(cantidad / 2);
            //         productos.forEach(function(p) {
            //             if (p['cantidad'] <= restantes) {
            //                 lineas[p['linea']].set_discount(100);
            //             } else {
            //                 lineas[p['linea']].set_discount(Math.floor(restantes/p['cantidad']*100));
            //             }
            //             restantes -= p['cantidad'];
            //         })
            //
            //     }
            // });

            distefanoButton.appendTo(this.$('.control-buttons'));
            this.$('.control-buttons').removeClass('oe_hidden');

            distefanoPaymentReference.appendTo(this.$('.payment-info'));
        },
    });

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

    // module.ClientListScreenWidget.include({
    //     // Shows,hides or edit the customer details box :
    //     // visibility: 'show', 'hide' or 'edit'
    //     // partner:    the partner object to show or edit
    //     // clickpos:   the height of the click on the list (in pixel), used
    //     //             to maintain consistent scroll.
    //     display_client_details: function(visibility,partner,clickpos){
    //         var self = this;
    //         var contents = this.$('.client-details-contents');
    //         var parent   = this.$('.client-list').parent();
    //         var scroll   = parent.scrollTop();
    //         var height   = contents.height();
    //
    //         contents.off('click','.button.edit');
    //         contents.off('click','.button.save');
    //         contents.off('click','.button.undo');
    //         contents.on('click','.button.edit',function(){ self.edit_client_details(partner); });
    //         contents.on('click','.button.save',function(){ self.save_client_details(partner); });
    //         contents.on('click','.button.undo',function(){ self.undo_client_details(partner); });
    //         this.editing_client = false;
    //         this.uploaded_picture = null;
    //
    //         if(visibility === 'show'){
    //             contents.empty();
    //             contents.append($(QWeb.render('ClientDetails',{widget:this,partner:partner})));
    //
    //             var new_height   = contents.height();
    //
    //             if(!this.details_visible){
    //                 if(clickpos < scroll + new_height + 20 ){
    //                     parent.scrollTop( clickpos - 20 );
    //                 }else{
    //                     parent.scrollTop(parent.scrollTop() + new_height);
    //                 }
    //             }else{
    //                 parent.scrollTop(parent.scrollTop() - height + new_height);
    //             }
    //
    //             this.details_visible = true;
    //             this.toggle_save_button();
    //         } else if (visibility === 'edit') {
    //             this.editing_client = true;
    //             contents.empty();
    //             contents.append($(QWeb.render('DistefanoClientDetailsEdit',{widget:this,partner:partner})));
    //             this.toggle_save_button();
    //
    //             contents.find('.image-uploader').on('change',function(){
    //                 self.load_image_file(event.target.files[0],function(res){
    //                     if (res) {
    //                         contents.find('.client-picture img, .client-picture .fa').remove();
    //                         contents.find('.client-picture').append("<img src='"+res+"'>");
    //                         contents.find('.detail.picture').remove();
    //                         self.uploaded_picture = res;
    //                     }
    //                 });
    //             });
    //         } else if (visibility === 'hide') {
    //             contents.empty();
    //             if( height > scroll ){
    //                 contents.css({height:height+'px'});
    //                 contents.animate({height:0},400,function(){
    //                     contents.css({height:''});
    //                 });
    //             }else{
    //                 parent.scrollTop( parent.scrollTop() - height);
    //             }
    //             this.details_visible = false;
    //             this.toggle_save_button();
    //         }
    //     },
    //     close: function(){
    //         this._super();
    //     },
    // })

};
