<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
    <!ENTITY lowercase "'abcdefghijklmnopqrstuvwxyz'">
    <!ENTITY uppercase "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'">
]>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule conv48to49 -->
<xsl:template match="*" mode="conv48to49">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv48to49"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>4.8</literal> to <literal>4.9</literal>.
</para>
<xsl:template match="image" mode="conv48to49">
    <xsl:choose>
        <!-- nothing to do if already at 4.9 -->
        <xsl:when test="@schemaversion > 4.8">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="4.9">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv48to49"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv48to49">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv48to49"/>
    </xsl:copy>
</xsl:template>

<!-- transform oem-dumphalt to oem-bootwait -->
<xsl:template match="oemconfig/oem-dumphalt" mode="conv48to49">
        <oem-bootwait><xsl:value-of select="text()"/></oem-bootwait>
</xsl:template>

</xsl:stylesheet>
