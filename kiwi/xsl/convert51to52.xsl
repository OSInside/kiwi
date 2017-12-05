<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv51to52">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv51to52"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<!-- remove inherit attribute from image -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.1</literal> to <literal>5.2</literal>.
</para>
<xsl:template match="image" mode="conv51to52">
    <xsl:choose>
        <!-- nothing to do if already at 5.2 -->
        <xsl:when test="@schemaversion > 5.1">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.2">
                <xsl:copy-of select="@*[local-name() != 'schemaversion' and local-name() != 'inherit']"/>
                <xsl:apply-templates  mode="conv51to52"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- remove obsolete usb image type -->
<xsl:template match="type" mode="conv51to52">
    <xsl:choose>
        <xsl:when test="@image!='usb'">
            <type>
            <xsl:copy-of select="@*"/>
            <xsl:apply-templates mode="conv51to52"/>
            </type>
        </xsl:when>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
