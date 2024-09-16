<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv52to53">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv52to53"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.2</literal> to <literal>5.3</literal>.
</para>
<xsl:template match="image" mode="conv52to53">
    <xsl:choose>
        <!-- nothing to do if already at 5.3-->
        <xsl:when test="@schemaversion > 5.2">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.3">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv52to53"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv52to53">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv52to53"/>
    </xsl:copy>
</xsl:template>

<!-- convert ec2region names -->
<xsl:template match="ec2region" mode="conv52to53">
    <xsl:variable name="regionval" select="text()"/>
    <xsl:choose>
        <xsl:when test="$regionval='AP-Japan'">
            <ec2region>AP-Northeast</ec2region>
        </xsl:when>
        <xsl:when test="$regionval='AP-Singapore'">
            <ec2region>AP-Southeast</ec2region>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="."/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
