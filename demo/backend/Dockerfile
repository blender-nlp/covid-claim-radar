# First stage, build the executable
FROM golang:1.13

ENV GOPROXY=https://goproxy.cn
ENV HOME=/opt/app

WORKDIR $HOME

COPY go.mod $HOME
COPY go.sum $HOME
RUN go mod download

COPY . $HOME
# Use static linking to get rid of the error below
# exec user process caused "no such file or directory"
RUN GOOS=linux GOARCH=amd64 go build -a -ldflags "-linkmode external -extldflags '-static' -s -w"

# Second stage for executable only image
FROM scratch

# Copy executable from the first stage
COPY --from=0 /opt/app/backend /backend
COPY --from=0 /opt/app/ind_keyword.ind /ind_keyword.ind
COPY --from=0 /opt/app/ind_name.ind /ind_name.ind
COPY --from=0 /opt/app/ind_title.ind /ind_title.ind
COPY --from=0 /opt/app/info.json /info.json
COPY --from=0 /opt/app/settings.ini /settings.ini

EXPOSE 80

CMD ["/backend"]
