<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
        xmlns:exslt="http://exslt.org/common"
        exclude-result-prefixes="exslt"
>

<xsl:import href="include.xsl"/>
<xsl:import href="convert74to75.xsl"/>
<xsl:import href="convert75to76.xsl"/>
<xsl:import href="convert76to80.xsl"/>
<xsl:import href="convert80to81.xsl"/>
<xsl:import href="convert81to82.xsl"/>
<xsl:import href="pretty.xsl"/>

<xsl:output encoding="utf-8" indent="yes"/>

<xsl:template match="/">
    <xsl:variable name="preprocess">
        <xsl:apply-templates select="/" mode="include"/>
    </xsl:variable>

    <xsl:variable name="v75">
        <xsl:apply-templates select="exslt:node-set($preprocess)" mode="conv74to75"/>
    </xsl:variable>

    <xsl:variable name="v76">
        <xsl:apply-templates select="exslt:node-set($v75)" mode="conv75to76"/>
    </xsl:variable>

    <xsl:variable name="v80">
        <xsl:apply-templates select="exslt:node-set($v76)" mode="conv76to80"/>
    </xsl:variable>

    <xsl:variable name="v81">
        <xsl:apply-templates select="exslt:node-set($v80)" mode="conv80to81"/>
    </xsl:variable>

    <xsl:variable name="v82">
        <xsl:apply-templates select="exslt:node-set($v81)" mode="conv81to82"/>
    </xsl:variable>

    <xsl:apply-templates
        select="exslt:node-set($v82)" mode="pretty"
    />
</xsl:template>

</xsl:stylesheet>
