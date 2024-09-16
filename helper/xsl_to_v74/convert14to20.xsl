<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv14to20">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv14to20"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemeversion</tag>
    from <literal>1.4</literal> to <literal>2.0</literal>. 
</para>
<xsl:template match="image" mode="conv14to20">
    <xsl:choose>
        <!-- nothing to do if already at 2.0 -->
        <xsl:when test="@schemeversion > 1.4 or @schemaversion > 1.4">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemeversion="2.0">
                <xsl:copy-of select="@*[local-name() != 'schemeversion']"/>
                <xsl:apply-templates mode="conv14to20"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv14to20">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv14to20"/>
    </xsl:copy>
</xsl:template>

<!-- split section update -->
<para xmlns="http://docbook.org/ns/docbook">
    Copy all attributes, when contents is NOT 'split'.
    If contents contains 'split' and attribute <tag class="attribute">
    filesystem</tag> contains a comma, then split this attribute and
    create two new attributes <tag class="attribute">fsreadwrite</tag>
    and <tag class="attribute">fsreadonly</tag>.
</para>
<xsl:template match="type" mode="conv14to20" >
    <xsl:variable name="fs" select="normalize-space(@filesystem)"/>
    <xsl:variable name="contents" select="."/>
    <type>
    <xsl:choose>
        <xsl:when test="$contents != 'split'">
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates mode="conv14to20"/>
        </xsl:when>
        <xsl:when test="$contents = 'split' and contains($fs, ',')">
            <xsl:attribute name="fsreadwrite">
            <xsl:value-of select="substring-before($fs, ',')"/>
            </xsl:attribute>
            <xsl:attribute name="fsreadonly">
            <xsl:value-of select="substring-after($fs, ',')"/>
            </xsl:attribute>
            <xsl:copy-of select="@boot"/>
            <xsl:copy-of select="@format"/>
            <xsl:apply-templates mode="conv14to20"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates mode="conv14to20"/>
        </xsl:otherwise>
    </xsl:choose>
    </type>
</xsl:template>

<!-- update boot / bootstrap -->
<para xmlns="http://docbook.org/ns/docbook"> 
    Change attribute value <tag class="attribute">boot</tag> to 
    <tag class="attribute">bootstrap</tag>.
</para>
<xsl:template match="packages[@type='boot']" mode="conv14to20">
    <packages type="bootstrap">
        <xsl:apply-templates mode="conv14to20"/>
    </packages>
</xsl:template>

</xsl:stylesheet>
