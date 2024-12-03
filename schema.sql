DROP TABLE IF EXISTS Customer_Service;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS Datas;
DROP TABLE IF EXISTS Device;
DROP TABLE IF EXISTS ServiceLocation;
DROP TABLE IF EXISTS Model;
DROP TABLE IF EXISTS Price;
DROP TABLE IF EXISTS user;

CREATE TABLE user
(
    cid        INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50)        NOT NULL,
    last_name  VARCHAR(50)        NOT NULL,
    username   VARCHAR(50) UNIQUE NOT NULL,
    password   VARCHAR(1000)      NOT NULL,
    billAddr   VARCHAR(4000)      NOT NULL
);


CREATE TABLE ServiceLocation
(
    sLid          INT PRIMARY KEY AUTO_INCREMENT,
    addr          VARCHAR(50) NOT NULL,
    zipcode       INT         NOT NULL,
    unitNumber    VARCHAR(20) NOT NULL,
    tookOverDate  DATE        NOT NULL,
    squareFootage INT         NOT NULL,
    bedroomCnt    INT         NOT NULL,
    occupantsCnt  INT         NOT NULL
);

CREATE TABLE Customer_Service
(
    cid  INT,
    sLid INT,
    PRIMARY KEY (cid, sLid),
    FOREIGN KEY (cid) REFERENCES user (cid),
    FOREIGN KEY (sLid) REFERENCES ServiceLocation (sLid)
);
CREATE TABLE Model
(
    modelid    INT PRIMARY KEY AUTO_INCREMENT,
    modeltype  VARCHAR(50) NOT NULL,
    modelname  VARCHAR(50) NOT NULL,
    properties VARCHAR(200)
);

CREATE TABLE Device
(
    deviceid INT PRIMARY KEY AUTO_INCREMENT,
    type     VARCHAR(100) NOT NULL,
    modelid  INT,
    SLid     INT,
    FOREIGN KEY (modelid) REFERENCES Model (modelid),
    FOREIGN KEY (sLid) REFERENCES ServiceLocation (sLid)
);

CREATE TABLE Datas
(
    dataid     INT PRIMARY KEY AUTO_INCREMENT,
    deviceid   INT,
    timestamp  DATETIME    NOT NULL,
    eventLabel VARCHAR(20) NOT NULL,
    value      FLOAT,
    FOREIGN KEY (deviceid) REFERENCES Device (deviceid)
);

CREATE TABLE Price
(
    fromtime TIME  NOT NULL,
    endtime  TIME  NOT NULL,
    zipcode  INT   NOT NULL,
    price    FLOAT NOT NULL,
    PRIMARY KEY (fromtime, endtime, zipcode)
);

DROP TABLE IF EXISTS Delivered;
DROP TABLE IF EXISTS ItemIn;
DROP TABLE IF EXISTS Ordered;
DROP TABLE IF EXISTS Piece;
DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Act;
DROP TABLE IF EXISTS Role;
DROP TABLE IF EXISTS DonatedBy;
DROP TABLE IF EXISTS PersonPhone;
DROP TABLE IF EXISTS Person;
DROP TABLE IF EXISTS Item;
DROP TABLE IF EXISTS Category;

CREATE TABLE Category (
    mainCategory VARCHAR(50),
    subCategory VARCHAR(50),
    catNotes TEXT,
    PRIMARY KEY (mainCategory, subCategory)
);

CREATE TABLE Item (
    itemID INT AUTO_INCREMENT PRIMARY KEY,
    iDescription TEXT,
    photo TEXT,
    color VARCHAR(30),
    isNew BOOLEAN,
    hasPieces BOOLEAN,
    material VARCHAR(50),
    mainCategory VARCHAR(50),
    subCategory VARCHAR(50),
    FOREIGN KEY (mainCategory, subCategory) REFERENCES Category(mainCategory, subCategory)
);


CREATE TABLE PersonPhone (
    userName VARCHAR(50),
    phone VARCHAR(15),
    FOREIGN KEY (userName) REFERENCES User(userName)
);

CREATE TABLE DonatedBy (
    itemID INT,
    userName VARCHAR(50),
    donateDate DATE,
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (userName) REFERENCES User(userName)
);

CREATE TABLE Role (
    roleID INT AUTO_INCREMENT PRIMARY KEY,
    rDescription TEXT
);

CREATE TABLE Act (
    userName VARCHAR(50),
    roleID INT,
    FOREIGN KEY (userName) REFERENCES User(userName),
    FOREIGN KEY (roleID) REFERENCES Role(roleID)
);

CREATE TABLE Location (
    roomNum VARCHAR(20),
    shelfNum VARCHAR(20),
    shelfDescription TEXT,
    PRIMARY KEY (roomNum, shelfNum)
);

CREATE TABLE Piece (
    itemID INT,
    pieceNum INT,
    pDescription TEXT,
    length FLOAT,
    width FLOAT,
    height FLOAT,
    roomNum VARCHAR(20),
    shelfNum VARCHAR(20),
    pNotes TEXT,
    PRIMARY KEY (itemID, pieceNum),
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (roomNum, shelfNum) REFERENCES Location(roomNum, shelfNum)
);

CREATE TABLE Ordered (
    orderID INT AUTO_INCREMENT PRIMARY KEY,
    orderDate DATE,
    orderNotes TEXT,
    supervisor VARCHAR(50),
    client VARCHAR(50),
    FOREIGN KEY (supervisor) REFERENCES User(userName),
    FOREIGN KEY (client) REFERENCES User(userName)
);

CREATE TABLE ItemIn (
    itemID INT,
    orderID INT,
    found BOOLEAN,
    FOREIGN KEY (itemID) REFERENCES Item(itemID),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);

CREATE TABLE Delivered (
    userName VARCHAR(50),
    orderID INT,
    status VARCHAR(50),
    date DATE,
    FOREIGN KEY (userName) REFERENCES User(userName),
    FOREIGN KEY (orderID) REFERENCES Ordered(orderID)
);
