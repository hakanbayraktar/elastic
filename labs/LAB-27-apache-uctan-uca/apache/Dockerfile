FROM httpd:2.4

RUN sed -i 's/^#LoadModule status_module /LoadModule status_module /' /usr/local/apache2/conf/httpd.conf \
    && sed -i 's/^\s*#LoadModule cgid_module /LoadModule cgid_module /' /usr/local/apache2/conf/httpd.conf \
    && printf '\nInclude conf/extra/apache-observability.conf\n' >> /usr/local/apache2/conf/httpd.conf

COPY conf/apache-observability.conf /usr/local/apache2/conf/extra/apache-observability.conf
COPY htdocs/ /usr/local/apache2/htdocs/
COPY cgi-bin/ /usr/local/apache2/cgi-bin/
RUN chmod 0755 /usr/local/apache2/cgi-bin/*.sh
