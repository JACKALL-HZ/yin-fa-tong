FROM rabbitmq:3.12-management

# Copy pre-downloaded delayed message exchange plugin
COPY rabbitmq_delayed_message_exchange-3.12.0.ez /plugins/

RUN chmod 0644 /plugins/rabbitmq_delayed_message_exchange-3.12.0.ez \
    && rabbitmq-plugins enable rabbitmq_delayed_message_exchange
